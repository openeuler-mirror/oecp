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
from oecp.result.compare_result import CompareResultComposite, CompareResultComponent
from oecp.result.constants import *

logger = logging.getLogger('oecp')


class CmdCompareExecutor(CompareExecutor):

    def __init__(self, dump_a, dump_b, config=None):
        super(CmdCompareExecutor, self).__init__(dump_a, dump_b, config)
        self.dump_a = dump_a.run()
        self.dump_b = dump_b.run()
        self.data = 'data'
        self.split_flag = '__rpm__'

    def _split_files(self, cmd_file):
        split_file = []
        if cmd_file:
            for file in cmd_file:
                split_file.append(file.split(self.split_flag)[-1])
        return split_file

    def _compare_result(self, dump_a, dump_b, single_result=CMP_RESULT_SAME):
        count_result = {'more_count': 0, 'less_count': 0, 'diff_count': 0}
        category = dump_a['category']
        result = CompareResultComposite(CMP_TYPE_RPM, single_result, dump_a['rpm'], dump_b['rpm'], category)
        file_a = self._split_files(dump_a[self.data])
        file_b = self._split_files(dump_b[self.data])
        if not file_a and not file_b:
            logger.debug(
                f"No {self.config.get('compare_type')} package found, ignored with {dump_b['rpm']} and {dump_b['rpm']}")
            return result
        component_results = self.format_dump(file_a, file_b)
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
        similar_dumpers = self.get_similar_rpm_pairs(self.dump_a, self.dump_b)
        for single_pair in similar_dumpers:
            if single_pair:
                dump_a, dump_b = single_pair[0], single_pair[1]
                result = self._compare_result(dump_a, dump_b)
                compare_list.append(result)
        return compare_list

    def run(self):
        result = self.compare()
        return result
