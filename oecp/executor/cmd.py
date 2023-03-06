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

    def _compare_result(self, dump_a, dump_b, single_result=CMP_RESULT_SAME):
        count_result = {'same': 0, 'more': 0, 'less': 0, 'diff': 0}
        category = dump_a['category']
        result = CompareResultComposite(CMP_TYPE_RPM, single_result, dump_a['rpm'], dump_b['rpm'], category)
        cmd_a_file = dump_a[self.data]
        cmd_b_file = dump_b[self.data]
        flag_v_r_d = self.extract_version_flag(dump_a['rpm'], dump_b['rpm'])
        if not cmd_a_file and not cmd_b_file:
            logger.debug(
                f"No {self.config.get('compare_type')} package found, ignored with {dump_a['rpm']} and {dump_b['rpm']}")
            return result
        component_results = self.format_dump(cmd_a_file, cmd_b_file, flag_v_r_d)
        for component_result in component_results:
            for sub_component_result in component_result:
                self.count_cmp_result(count_result, sub_component_result[-1])
                if not self.config.get('show_same', False) and sub_component_result[-1] == CMP_RESULT_SAME:
                    continue
                data = CompareResultComponent(self.config.get('compare_type'), sub_component_result[-1],
                                              sub_component_result[0], sub_component_result[1])
                if sub_component_result[-1] not in CMP_SAME_RESULT and single_result == CMP_RESULT_SAME:
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
