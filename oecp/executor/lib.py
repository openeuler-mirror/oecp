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

from oecp.executor.base import CompareExecutor
from oecp.proxy.rpm_proxy import RPMProxy
from oecp.result.compare_result import CompareResultComposite, CompareResultComponent
from oecp.result.constants import CMP_RESULT_SAME, CMP_TYPE_RPM, CMP_RESULT_DIFF, CMP_RESULT_CHANGE, CMP_TYPE_RPM_LIB

logger = logging.getLogger('oecp')


class LibCompareExecutor(CompareExecutor):

    def __init__(self, dump_a, dump_b, config=None):
        super(LibCompareExecutor, self).__init__(dump_a, dump_b, config)
        self.dump_a = dump_a.run()
        self.dump_b = dump_b.run()
        self.data = 'data'

    def _compare_result(self, dump_a, dump_b, single_result=CMP_RESULT_SAME):
        count_result = {'more_count': 0, 'less_count': 0, 'diff_count': 0}
        category = dump_a['category']
        result = CompareResultComposite(CMP_TYPE_RPM, single_result, dump_a['rpm'], dump_b['rpm'], category)
        base_lib_files = dump_a[self.data]
        other_lib_file = dump_b[self.data]
        flag_vrd = self.extract_version_flag(dump_a['rpm'], dump_b['rpm'])
        if not base_lib_files and not other_lib_file:
            logger.debug(
                f"No {self.config.get('compare_type')} package found, ignored with {dump_b['rpm']} and {dump_b['rpm']}")
            return result
        component_results = self.match_library_pairs(base_lib_files, other_lib_file, flag_vrd, CMP_TYPE_RPM_LIB)
        for component_result in component_results:
            for sub_component_result in component_result:
                if not self.config.get('show_same', False) and sub_component_result[-1] == CMP_RESULT_SAME:
                    continue
                if sub_component_result[-1] == 'more':
                    count_result["more_count"] += 1
                elif sub_component_result[-1] == 'less':
                    count_result["less_count"] += 1
                data = CompareResultComponent(self.config.get('compare_type'), sub_component_result[-1],
                                              sub_component_result[0], sub_component_result[1])
                if sub_component_result[-1] not in [CMP_RESULT_SAME,
                                                    CMP_RESULT_CHANGE] and single_result == CMP_RESULT_SAME:
                    single_result = CMP_RESULT_DIFF
                    result.set_cmp_result(single_result)
                result.add_component(data)
        result.add_count_info(count_result)

        return result

    def compare(self):
        compare_list = []
        for dump_a in self.dump_a:
            for dump_b in self.dump_b:
                # 取rpm name 相同进行比较
                if RPMProxy.rpm_name(dump_a['rpm']) == RPMProxy.rpm_name(dump_b['rpm']):
                    result = self._compare_result(dump_a, dump_b)
                    compare_list.append(result)
        return compare_list

    def run(self):
        result = self.compare()
        return result
