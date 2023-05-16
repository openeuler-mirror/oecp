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
from oecp.result.constants import COUNT_ABI_DETAILS, PAT_SO, CMP_RESULT_CHANGE
from oecp.executor.base import CompareExecutor

logger = logging.getLogger('oecp')


class ABICompareExecutor(CompareExecutor):

    def __init__(self, base_dump, other_dump, config):
        super(ABICompareExecutor, self).__init__(base_dump, other_dump, config)
        self.base_dump = base_dump.run()
        self.other_dump = other_dump.run()
        self.data = 'data'
        self.link_file = 'link_file'

    @staticmethod
    def compare_link_files(base_dump_linkfiles, other_dump_linkfiles, rpm):
        for base_linkfile in base_dump_linkfiles:
            for other_linkfile in other_dump_linkfiles:
                if base_linkfile[0] == other_linkfile[0]:
                    if base_linkfile[1] == other_linkfile[1]:
                        continue
                    else:
                        logger.info(f"{rpm} {base_linkfile[0]} link file is change!")

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

    @staticmethod
    def _get_soname(library_file):
        cmd = f'objdump -p {library_file}'
        ret, out, err = shell_cmd(cmd.split())
        if not ret and out:
            match = re.search(r'SONAME\s(.+)\s', out)
            if match:
                so_name = match.groups()[0].strip()
                return so_name

        return library_file

    def get_library_pairs(self, base_file, other_file):
        base_soname = self._get_soname(base_file)
        other_soname = self._get_soname(other_file)
        if base_soname == other_soname:
            return True

        return False

    def get_common_lib_pairs(self, base_datas, other_datas, flag_vrd):
        dump_os_changed, dump_exist = [], []
        base_files, other_files = set(base_datas.keys()), set(other_datas.keys())
        common_dump = base_files & other_files
        only_dump_base = base_files - other_files
        only_dump_other = other_files - base_files
        so_pattern = re.compile(PAT_SO)
        for other_so in sorted(only_dump_other):
            for base_so in sorted(only_dump_base):
                if base_so in dump_exist:
                    continue
                os_base_name, os_other_name = os.path.basename(base_so), os.path.basename(other_so)
                cut_base_name = re.sub(so_pattern, '', os_base_name)
                cut_other_name = re.sub(so_pattern, '', os_other_name)
                if cut_base_name.lstrip('_') != cut_other_name.lstrip('_'):
                    continue
                full_base_so = base_datas.get(base_so)
                full_other_so = other_datas.get(other_so)
                path_result = self.get_version_change_files(base_so, other_so, flag_vrd)
                soname_result = self.get_library_pairs(full_base_so, full_other_so)
                if path_result == CMP_RESULT_CHANGE or soname_result:
                    dump_os_changed.append([full_base_so, full_other_so])
                    dump_exist.append(base_so)
                    break

        common_so = [[base_datas.get(so), other_datas.get(so)] for so in common_dump]
        common_so.extend(dump_os_changed)

        return common_so

    def compare_result(self, base_dump, other_dump, single_result=CMP_RESULT_SAME):
        count_result = {'same': 0, 'more': 0, 'less': 0, 'diff': 0}
        count_result.update(COUNT_ABI_DETAILS)
        base_rpm, other_rpm = base_dump['rpm'], other_dump['rpm']
        result = CompareResultComposite(CMP_TYPE_RPM, single_result, base_rpm, other_rpm, base_dump['category'])
        base_debuginfo_path, other_debuginfo_path = base_dump['debuginfo_extract_path'], other_dump[
            'debuginfo_extract_path']
        map_files_a = self.split_files_mapping(base_dump[self.data])
        map_files_b = self.split_files_mapping(other_dump[self.data])
        flag_vrd = self.extract_version_flag(base_dump['rpm'], other_dump['rpm'])
        library_pairs = self.get_common_lib_pairs(map_files_a, map_files_b, flag_vrd)

        if not library_pairs:
            return result
        base_debuginfo_path = os.path.join(base_debuginfo_path, 'usr/lib/debug') if base_debuginfo_path else ''
        other_debuginfo_path = os.path.join(other_debuginfo_path, 'usr/lib/debug') if other_debuginfo_path else ''
        for pair in library_pairs:
            base_so = os.path.basename(pair[0])
            other_so = os.path.basename(pair[1])
            if all([base_debuginfo_path, other_debuginfo_path]):
                cmd = "abidiff {} {} --d1 {} --d2 {} --no-unreferenced-symbols --changed-fns --deleted-fns".format(
                    pair[0], pair[1], base_debuginfo_path, other_debuginfo_path)
            else:
                cmd = "abidiff {} {} --changed-fns --deleted-fns".format(pair[0], pair[1])

            logger.debug(cmd)
            ret, out, err = shell_cmd(cmd.split())
            if ret == 0:
                logger.debug("check abi same")
                self.count_cmp_result(count_result, CMP_RESULT_SAME)
                data = CompareResultComponent(CMP_TYPE_RPM_ABI, CMP_RESULT_SAME, base_so, other_so)
            else:
                logger.debug("check abi diff")
                removed_abi, changed_abi, added_abi = self.extract_abi_change_detail(out)
                count_result['remove_abi'] += removed_abi
                count_result['change_abi'] += changed_abi
                count_result['add_abi'] += added_abi
                if changed_abi or removed_abi:
                    self.count_cmp_result(count_result, CMP_RESULT_DIFF)
                    data = CompareResultComponent(CMP_TYPE_RPM_ABI, CMP_RESULT_DIFF, base_so, other_so, detail_file=out)
                    result.set_cmp_result(CMP_RESULT_DIFF)
                else:
                    logger.debug("check abi functions that are not deleted or changed.")
                    self.count_cmp_result(count_result, CMP_RESULT_SAME)
                    data = CompareResultComponent(CMP_TYPE_RPM_ABI, CMP_RESULT_SAME, base_so, other_so, detail_file=out)
            result.add_component(data)
        base_dump_linkfiles, other_dump_linkfiles = base_dump[self.link_file], other_dump[self.link_file]
        self.compare_link_files(base_dump_linkfiles, other_dump_linkfiles, base_rpm)
        result.add_count_info(count_result)

        return result

    def compare(self):
        compare_list = []
        similar_dumpers = self.get_similar_rpm_pairs(self.base_dump, self.other_dump)
        for single_pair in similar_dumpers:
            if single_pair:
                # dump_a: single_pair[0], dump_b: single_pair[1]
                result = self.compare_result(single_pair[0], single_pair[1])
                logger.debug(result)
                compare_list.append(result)
        return compare_list

    def run(self):
        result = self.compare()
        return result
