# -*- encoding=utf-8 -*-
"""
# **********************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# [oecp] is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# **********************************************************************************
"""

import logging
import os
import re

from oecp.utils.shell import shell_cmd
from oecp.result.compare_result import CMP_RESULT_SAME, CompareResultComposite, CMP_TYPE_RPM, CMP_TYPE_RPM_ABI, \
    CompareResultComponent, CMP_RESULT_DIFF
from oecp.result.constants import DETAIL_PATH, COUNT_ABI_DETAILS
from oecp.executor.base import CompareExecutor

logger = logging.getLogger('oecp')


class ABICompareExecutor(CompareExecutor):

    def __init__(self, dump_a, dump_b, config):
        super(ABICompareExecutor, self).__init__(dump_a, dump_b, config)
        self.dump_a = dump_a.run()
        self.dump_b = dump_b.run()
        cache_require_key = 'extract'
        self._work_dir = self.config.get(cache_require_key, {}).get('work_dir', DETAIL_PATH)
        self.data = 'data'
        self.split_flag = '__rpm__'
        self.link_file = 'link_file'

    @staticmethod
    def _set_so_mapping(library_files):
        if not library_files:
            return {}

        so_mapping = {}
        for library_file in library_files:
            cmd = f'objdump -p {library_file}'
            ret, out, err = shell_cmd(cmd.split())
            if not ret and out:
                match = re.search(r'SONAME\s(.+)\s', out)
                if match:
                    so_name = match.groups()[0].strip()
                    so_mapping.setdefault(so_name, library_file)
        return so_mapping

    def _get_library_pairs(self, files_a, files_b):
        library_pairs = []
        so_mapping_a = self._set_so_mapping(files_a)
        so_mapping_b = self._set_so_mapping(files_b)
        for so_name in so_mapping_a:
            if so_name in so_mapping_b:
                library_pairs.append([so_mapping_a[so_name], so_mapping_b[so_name]])
        return library_pairs

    @staticmethod
    def compare_link_files(dump_a_linkfiles, dump_b_linkfiles, rpm):
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
    def extract_abi_change_detail(str_content):
        remove_abi, change_abi, add_abi = 0, 0, 0
        pattern_db = r"Functions changes summary: (\d+) Removed(.*?), (\d+) Changed(.*?), (\d+) Added(.*?)functions?"
        debug_match = re.finditer(pattern_db, str_content)
        for d_match in debug_match:
            if d_match:
                remove_abi += int(d_match.group(1))
                change_abi += int(d_match.group(3))
                add_abi += int(d_match.group(5))
        pattern_ndb = r"Function(.*?)summary: (\d+) Removed, (\d+) Added(.*?)debug info"
        no_debug_match = re.finditer(pattern_ndb, str_content)
        for n_match in no_debug_match:
            if n_match:
                remove_abi += int(n_match.group(2))
                add_abi += int(n_match.group(3))
        return remove_abi, change_abi, add_abi

    def _compare_result(self, dump_a, dump_b, single_result=CMP_RESULT_SAME):
        count_result = {'same': 0, 'more': 0, 'less': 0, 'diff': 0}
        count_result.update(COUNT_ABI_DETAILS)
        kind = dump_a['kind']
        rpm_a, rpm_b = dump_a['rpm'], dump_b['rpm']
        result = CompareResultComposite(CMP_TYPE_RPM, single_result, rpm_a, rpm_b, dump_a['category'])
        debuginfo_rpm_path_a, debuginfo_rpm_path_b = dump_a['debuginfo_extract_path'], dump_b['debuginfo_extract_path']

        dump_a_files, dump_b_files = dump_a[self.data], dump_b[self.data]
        library_pairs = self._get_library_pairs(dump_a_files, dump_b_files)
        if not library_pairs:
            return result
        debuginfo_rpm_path_a = os.path.join(debuginfo_rpm_path_a, 'usr/lib/debug') if debuginfo_rpm_path_a else ''
        debuginfo_rpm_path_b = os.path.join(debuginfo_rpm_path_b, 'usr/lib/debug') if debuginfo_rpm_path_b else ''

        verbose_cmp_path = f'{rpm_a}__cmp__{rpm_b}'
        base_dir = os.path.join(self._work_dir, kind, verbose_cmp_path)
        for pair in library_pairs:
            base_a = os.path.basename(pair[0])
            base_b = os.path.basename(pair[1])
            if all([debuginfo_rpm_path_a, debuginfo_rpm_path_b]):
                cmd = "abidiff {} {} --d1 {} --d2 {} --no-unreferenced-symbols --changed-fns --deleted-fns".format(
                    pair[0], pair[1], debuginfo_rpm_path_a, debuginfo_rpm_path_b)
            else:
                cmd = "abidiff {} {} --d1 {} --d2 {} --changed-fns --deleted-fns".format(
                    pair[0], pair[1], debuginfo_rpm_path_a, debuginfo_rpm_path_b)

            logger.debug(cmd)
            ret, out, err = shell_cmd(cmd.split())
            if ret == 0:
                logger.debug("check abi same")
                self.count_cmp_result(count_result, CMP_RESULT_SAME)
                data = CompareResultComponent(CMP_TYPE_RPM_ABI, CMP_RESULT_SAME, base_a, base_b)
            else:
                if not os.path.exists(base_dir):
                    os.makedirs(base_dir)
                file_path = os.path.join(base_dir, f'{base_a}__cmp__{base_b}.md')
                self._save_result(file_path, out)
                logger.debug("check abi diff")
                removed_abi, changed_abi, added_abi = self.extract_abi_change_detail(out)
                count_result['remove_abi'] += removed_abi
                count_result['change_abi'] += changed_abi
                count_result['add_abi'] += added_abi
                if changed_abi or removed_abi:
                    self.count_cmp_result(count_result, CMP_RESULT_DIFF)
                    data = CompareResultComponent(CMP_TYPE_RPM_ABI, CMP_RESULT_DIFF, base_a, base_b, file_path)
                    result.set_cmp_result(CMP_RESULT_DIFF)
                else:
                    logger.debug("check abi functions that are not deleted or changed.")
                    self.count_cmp_result(count_result, CMP_RESULT_SAME)
                    data = CompareResultComponent(CMP_TYPE_RPM_ABI, CMP_RESULT_SAME, base_a, base_b)
            result.add_component(data)
        dump_a_linkfiles, dump_b_linkfiles = dump_a[self.link_file], dump_b[self.link_file]
        self.compare_link_files(dump_a_linkfiles, dump_b_linkfiles, rpm_a)
        result.add_count_info(count_result)

        return result

    def compare(self):
        compare_list = []
        similar_dumpers = self.get_similar_rpm_pairs(self.dump_a, self.dump_b)
        for single_pair in similar_dumpers:
            if single_pair:
                # dump_a: single_pair[0], dump_b: single_pair[1]
                result = self._compare_result(single_pair[0], single_pair[1])
                logger.debug(result)
                compare_list.append(result)
        return compare_list

    def run(self):
        result = self.compare()
        return result
