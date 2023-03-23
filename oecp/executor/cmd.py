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

    def __init__(self, base_dump, other_dump, config=None):
        super(CmdCompareExecutor, self).__init__(base_dump, other_dump, config)
        self.base_dump = base_dump.run()
        self.other_dump = other_dump.run()
        self.data = 'data'

    def compare_result(self, base_dump, other_dump, single_result=CMP_RESULT_SAME):
        count_result = {'same': 0, 'more': 0, 'less': 0, 'diff': 0}
        category = base_dump['category']
        result = CompareResultComposite(CMP_TYPE_RPM, single_result, base_dump['rpm'], other_dump['rpm'], category)
        base_cmd_files = base_dump[self.data]
        other_cmd_files = other_dump[self.data]
        flag_v_r_d = self.extract_version_flag(base_dump['rpm'], other_dump['rpm'])
        if not base_cmd_files and not other_cmd_files:
            logger.debug(
                f"No {self.config.get('compare_type')} package found, "
                f"ignored with {base_dump['rpm']} and {other_dump['rpm']}")
            return result
        component_results = self.format_dump(base_cmd_files, other_cmd_files, flag_v_r_d)
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
        similar_dumpers = self.get_similar_rpm_pairs(self.base_dump, self.other_dump)
        for single_pair in similar_dumpers:
            if single_pair:
                base_dump, other_dump = single_pair[0], single_pair[1]
                result = self.compare_result(base_dump, other_dump)
                compare_list.append(result)
        return compare_list

    def run(self):
        result = self.compare()
        return result
