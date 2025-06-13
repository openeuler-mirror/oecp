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
from oecp.result.compare_result import CompareResultComponent, CompareResultComposite, CMP_TYPE_RPM, CMP_RESULT_DIFF
from oecp.result.constants import JABI_TEMP_PATH, DETAIL_PATH, CMP_TYPE_RPM_JABI, CMP_RESULT_SAME
from oecp.executor.base import CompareExecutor
from oecp.utils.common import remove_duplicate_files

logger = logging.getLogger('oecp')


class JABICompareExecutor(CompareExecutor):

    def __init__(self, base_dump, other_dump, config):
        super(JABICompareExecutor, self).__init__(base_dump, other_dump, config)
        self.base_dump = base_dump.run()
        self.other_dump = other_dump.run()
        self.data = 'data'

    @staticmethod
    def _executive_cmd(base_dir, file_list, count_result, result_components, lock):
        try:
            base_a = os.path.basename(file_list[0])
            base_b = os.path.basename(file_list[1])
            path_prefix = f"{base_a.split('.')[0]}_cmp_{base_b.split('.')[0]}"
            file_path = os.path.join(base_dir, f'{path_prefix}__compat_report.html')
            cmd = "japi-compliance-checker -bin -lib common {} {} -report-path {}".format(file_list[0], file_list[1],
                                                                                          file_path)
            ret, out, err = shell_cmd(cmd.split())

            if not ret and out:
                match = re.search(r'Binary compatibility: (.+)\s', out)
                if match:
                    compat_result = match.groups()[0]
                    data = CompareResultComponent(
                        CMP_TYPE_RPM_JABI, compat_result, base_a, base_b, file_path)
                    with lock:
                        if compat_result != '100%':
                            count_result["diff_count"] += 1
                        result_components.extend([data])
        except Exception as e:
            logger.exception(f"compare jabi error,detail:{e}")

    def _compare_result(self, base_dump, other_dump, single_result=CMP_RESULT_SAME):
        kind = base_dump['kind']
        base_rpm, other_rpm = base_dump['rpm'], other_dump['rpm']
        count_result = {'same': 0, 'more': 0, 'less': 0, 'diff': 0}
        result = CompareResultComposite(CMP_TYPE_RPM, single_result, base_rpm, other_rpm, base_dump['category'])
        base_files, other_files = remove_duplicate_files(base_dump[self.data]), remove_duplicate_files(
            other_dump[self.data])
        flag_vrd = self.extract_version_flag(base_dump['rpm'], other_dump['rpm'])
        common_file_pairs = self.match_library_pairs(base_files, other_files, flag_vrd, CMP_TYPE_RPM_JABI)
        if not common_file_pairs:
            logger.debug("No jar package found, ignored with %s and %s", base_rpm, other_rpm)
            return result
        base_dir = os.path.join(JABI_TEMP_PATH, other_rpm)
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        for pair in common_file_pairs:
            base_file = pair[0].split(self.split_flag)[-1]
            other_file = pair[1].split(self.split_flag)[-1]
            other_name = re.sub('/', '-', other_file).lstrip('-')
            path_prefix = f"{other_name}_compat_report.html"
            file_path = os.path.join(base_dir, path_prefix)
            cmd = "japi-compliance-checker -bin -lib common {} {} -report-path {}".format(pair[0], pair[1], file_path)
            detail_path = os.path.join(DETAIL_PATH, kind, other_rpm, path_prefix)
            ret, out, err = shell_cmd(cmd.split())
            if err:
                logger.error(f"japi-compliance-checker compare {base_file} and {other_file} error: {err}")
            if out:
                match = re.search(r'Binary compatibility: (.+)\s', out)
                if match:
                    compare_result = match.groups()[0]
                    if compare_result == '100%':
                        self.count_cmp_result(count_result, CMP_RESULT_SAME)
                    else:
                        self.count_cmp_result(count_result, CMP_RESULT_DIFF)
                        result.set_cmp_result(CMP_RESULT_DIFF)
                    data = CompareResultComponent(CMP_TYPE_RPM_JABI, compare_result, base_file, other_file, detail_path)
                    result.add_component(data)
        result.add_count_info(count_result)

        return result

    def compare(self):
        result_list = []
        similar_dumpers = self.get_similar_rpm_pairs(self.base_dump, self.other_dump)
        for single_pair in similar_dumpers:
            if single_pair:
                base_dump, other_dump = single_pair[0], single_pair[1]
                result = self._compare_result(base_dump, other_dump)
                result_list.append(result)
        return result_list

    def run(self):
        result = self.compare()
        return result
