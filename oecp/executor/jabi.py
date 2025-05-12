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

from oecp.utils.shell import shell_cmd
from oecp.proxy.rpm_proxy import RPMProxy
from oecp.result.compare_result import CMP_RESULT_SAME, CompareResultComposite, CMP_TYPE_RPM, CMP_TYPE_RPM_JABI, \
    CompareResultComponent, CMP_RESULT_DIFF
from oecp.executor.base import CompareExecutor
from oecp.utils.common import remove_duplicate_files

logger = logging.getLogger('oecp')


class JABICompareExecutor(CompareExecutor):

    def __init__(self, dump_a, dump_b, config):
        super(JABICompareExecutor, self).__init__(dump_a, dump_b, config)
        self.dump_a = dump_a.run()
        self.dump_b = dump_b.run()
        self._work_dir = self.config.get('detail_path')

    def _executive_cmd(self, base_dir, file_list, count_result, result_components, lock):
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

    def _compare_result(self, dump_a, dump_b, single_result=CMP_RESULT_SAME):
        kind = dump_a['kind']
        rpm_a, rpm_b = dump_a['rpm'], dump_b['rpm']
        count_result = {'more_count': 0, 'less_count': 0, 'diff_count': 0}
        result = CompareResultComposite(CMP_TYPE_RPM, single_result, rpm_a, rpm_b, dump_a['category'])
        dump_a_files, dump_b_files = remove_duplicate_files(dump_a[self.data]), remove_duplicate_files(
            dump_b[self.data])
        flag_vrd = self.extract_version_flag(dump_a['rpm'], dump_b['rpm'])
        common_file_pairs = self.match_library_pairs(dump_a_files, dump_b_files, flag_vrd, CMP_TYPE_RPM_JABI)
        if not common_file_pairs:
            logger.debug("No jar package found, ignored with %s and %s", rpm_a, rpm_b)
            return result
        verbose_cmp_path = f'{rpm_a}__cmp__{rpm_b}'
        base_dir = os.path.join(self._work_dir, kind, verbose_cmp_path)
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        for pair in common_file_pairs:
            base_a = os.path.basename(pair[0])
            base_b = os.path.basename(pair[1])
            path_prefix = f"{base_a.split('.')[0]}_cmp_{base_b.split('.')[0]}"
            file_path = os.path.join(base_dir, f'{path_prefix}__compat_report.html')
            cmd = "japi-compliance-checker -bin -lib common {} {} -report-path {}".format(pair[0], pair[1], file_path)
            ret, out, err = shell_cmd(cmd.split())

            if err:
                logger.error(f"japi-compliance-checker compare {base_a} and {base_b} error: {err}")
            if out:
                match = re.search(r'Binary compatibility: (.+)\s', out)
                if match:
                    compat_result = match.groups()[0]
                    if compat_result == '100%':
                        data = CompareResultComponent(CMP_TYPE_RPM_JABI, CMP_RESULT_SAME, base_a, base_b, file_path)
                    else:
                        count_result["diff_count"] += 1
                        data = CompareResultComponent(CMP_TYPE_RPM_JABI, CMP_RESULT_DIFF, base_a, base_b, file_path)
                        result.set_cmp_result(CMP_RESULT_DIFF)
                    result.add_component(data)
        logger.info(f"Complete jabi compare {base_a} with {base_b}")
        result.add_count_info(count_result)

        return result

    def compare(self):
        result_list = []
        for dump_a in self.dump_a:
            for dump_b in self.dump_b:
                # 取rpm name 相同进行比较
                if RPMProxy.rpm_name(dump_a['rpm']) == RPMProxy.rpm_name(dump_b['rpm']):
                    result = self._compare_result(dump_a, dump_b)
                    result_list.append(result)
        return result_list

    def run(self):
        result = self.compare()
        return result
