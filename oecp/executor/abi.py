# -*- encoding=utf-8 -*-
"""
# **********************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# [oecp] is licensed under the Mulan PSL v1.
# You can use this software according to the terms and conditions of the Mulan PSL v1.
# You may obtain a copy of Mulan PSL v1 at:
#     http://license.coscl.org.cn/MulanPSL
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v1 for more details.
# **********************************************************************************
"""

import logging
import os
import re

from collections import defaultdict
from subprocess import TimeoutExpired

from oecp.utils.shell import shell_cmd
from oecp.proxy.rpm_proxy import RPMProxy
from oecp.result.compare_result import CMP_RESULT_SAME, CompareResultComposite, CMP_TYPE_RPM, CMP_TYPE_RPM_ABI, \
    CompareResultComponent, CMP_RESULT_DIFF
from oecp.executor.base import CompareExecutor

logger = logging.getLogger('oecp')


class ABICompareExecutor(CompareExecutor):

    def __init__(self, dump_a, dump_b, config):
        super(ABICompareExecutor, self).__init__(dump_a, dump_b, config)
        self.dump_a = dump_a.run()
        self.dump_b = dump_b.run()
        self._work_dir = self.config.get('detail_path')
        self.link_file = 'link_file'

    def compare_link_files(self, dump_a_linkfiles, dump_b_linkfiles, rpm):
        for file_a in dump_a_linkfiles:
            for file_b in dump_b_linkfiles:
                if file_a[0] == file_b[0]:
                    if file_a[1] == file_b[1]:
                        continue
                    else:
                        logger.info(f"{rpm} {file_a[0]} link file is change!")

    @staticmethod
    def _save_result(file_path, content):
        with open(file_path, "w") as f:
            f.write(content)

    @staticmethod
    def _extract_changed_abi(string_content):
        changed_abi = []
        pattern = r"function(.*)at(.*)changes:"
        all_match = re.finditer(pattern, string_content)
        for match in all_match:
            if match:
                changed_abi.append(match.group(1))
        return changed_abi

    @staticmethod
    def _extract_deleted_abi(string_content):
        deleted_abi = []
        pattern = r"'function(.*?)'\s+{\w+@@[0-9a-zA-Z._]+}"
        all_match = re.finditer(pattern, string_content, flags=re.S)
        for match in all_match:
            if match:
                deleted_abi.append(match.group(1))
        return deleted_abi

    def abidiff_common_pairs(self, pair, debug_paths):
        # 设定returncode初始值，不含debuginfo调试信息abidiff比较超时则该特定值不变
        returncode = 4
        out, err = "", ""
        try:
            if all(debug_paths):
                cmd = "abidiff {} {} --d1 {} --d2 {} --no-unreferenced-symbols --changed-fns --deleted-fns".format(
                    pair[0], pair[1], debug_paths[0], debug_paths[1])
            else:
                cmd = "abidiff {} {} --changed-fns --deleted-fns".format(pair[0], pair[1])
            logger.debug(cmd)
            returncode, out, err = shell_cmd(cmd.split(), timeout=1800)
        except TimeoutExpired as error:
            logger.error(f"TimeoutExpired Error: {error}")
            if all(debug_paths):
                returncode, out, err = self.abidiff_common_pairs(pair, ['', ''])

        return returncode, out, err

    def _compare_result(self, dump_a, dump_b, single_result=CMP_RESULT_SAME):
        count_result = {'more_count': 0, 'less_count': 0, 'diff_count': 0}
        kind = dump_a['kind']
        rpm_a, rpm_b = dump_a['rpm'], dump_b['rpm']
        result = CompareResultComposite(CMP_TYPE_RPM, single_result, rpm_a, rpm_b, dump_a['category'])
        debuginfo_rpm_path_a, debuginfo_rpm_path_b = dump_a['debuginfo_extract_path'], dump_b['debuginfo_extract_path']
        flag_vrd = self.extract_version_flag(dump_a['rpm'], dump_b['rpm'])
        dump_a_files, dump_b_files = dump_a[self.data], dump_b[self.data]
        library_pairs = self.match_library_pairs(dump_a_files, dump_b_files, flag_vrd, CMP_TYPE_RPM_ABI)
        if not library_pairs:
            return result
        debuginfo_rpm_path_a = os.path.join(debuginfo_rpm_path_a, 'usr/lib/debug') if debuginfo_rpm_path_a else ''
        debuginfo_rpm_path_b = os.path.join(debuginfo_rpm_path_b, 'usr/lib/debug') if debuginfo_rpm_path_b else ''

        verbose_cmp_path = f'{rpm_a}__cmp__{rpm_b}'
        base_dir = os.path.join(self._work_dir, kind, verbose_cmp_path)
        for pair in library_pairs:
            base_a = os.path.basename(pair[0])
            base_b = os.path.basename(pair[1])
            ret, out, err = self.abidiff_common_pairs(pair, [debuginfo_rpm_path_a, debuginfo_rpm_path_b])
            if not out:
                if ret == 4:
                    logger.warning(f"Compare {pair} abi 30 minutes overtime.")
                    continue
                else:
                    logger.debug("%s Check abi same and retruncode == %s", pair, ret)
                    data = CompareResultComponent(CMP_TYPE_RPM_ABI, CMP_RESULT_SAME, base_a, base_b)
                    result.add_component(data)
            else:
                abi = defaultdict(list)
                if not os.path.exists(base_dir):
                    os.makedirs(base_dir)
                file_path = os.path.join(base_dir, f'{base_a}__cmp__{base_b}.md')
                self._save_result(file_path, out)
                logger.debug("check abi diff")
                changed_abi, deleted_abi = self._extract_changed_abi(out), self._extract_deleted_abi(out)
                abi["changed_abi"] = changed_abi
                abi["deleted_abi"] = deleted_abi
                data = CompareResultComponent(CMP_TYPE_RPM_ABI, CMP_RESULT_DIFF, base_a, base_b, {file_path: abi})
                count_result["diff_count"] += 1
                result.set_cmp_result(CMP_RESULT_DIFF)
                result.add_component(data)
        dump_a_linkfiles, dump_b_linkfiles = dump_a[self.link_file], dump_b[self.link_file]
        self.compare_link_files(dump_a_linkfiles, dump_b_linkfiles, rpm_a)
        result.add_count_info(count_result)

        return result

    def compare(self):
        compare_list = []
        for dump_a in self.dump_a:
            for dump_b in self.dump_b:
                # 取rpm name 相同进行比较
                if RPMProxy.rpm_name(dump_a['rpm']) == RPMProxy.rpm_name(dump_b['rpm']):
                    result = self._compare_result(dump_a, dump_b)
                    logger.debug(result)
                    compare_list.append(result)
        return compare_list

    def run(self):
        result = self.compare()
        return result
