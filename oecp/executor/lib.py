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
from oecp.result.constants import CMP_RESULT_SAME, CMP_TYPE_RPM, CMP_SAME_RESULT, CMP_RESULT_DIFF, CMP_TYPE_RPM_LIB

logger = logging.getLogger('oecp')


class LibCompareExecutor(CompareExecutor):

    def __init__(self, dump_base, dump_other, config=None):
        super(LibCompareExecutor, self).__init__(dump_base, dump_other, config)
        self.dump_base = dump_base.run()
        self.dump_other = dump_other.run()
        self.data = 'data'

    def compare_result(self, dump_base, dump_other, single_result=CMP_RESULT_SAME):
        count_result = {'same': 0, 'more': 0, 'less': 0, 'diff': 0}
        category = dump_base['category']
        cmp_type = self.config.get('compare_type')
        result = CompareResultComposite(CMP_TYPE_RPM, single_result, dump_base['rpm'], dump_other['rpm'], category)
        base_libs = dump_base[self.data]
        other_libs = dump_other[self.data]
        flag_vrd = self.extract_version_flag(dump_base['rpm'], dump_other['rpm'])
        if not base_libs and not other_libs:
            logger.debug(f"No {cmp_type} package found, ignored with {dump_base['rpm']} and {dump_other['rpm']}")
            return result
        component_results = self.match_library_pairs(base_libs, other_libs, flag_vrd, CMP_TYPE_RPM_LIB)
        for component_result in component_results:
            for sub_component_result in component_result:
                self.count_cmp_result(count_result, sub_component_result[-1])
                if not self.config.get('show_same', False) and sub_component_result[-1] == CMP_RESULT_SAME:
                    continue
                data = CompareResultComponent(cmp_type, sub_component_result[-1], sub_component_result[0],
                                              sub_component_result[1])
                if sub_component_result[-1] not in CMP_SAME_RESULT and single_result == CMP_RESULT_SAME:
                    single_result = CMP_RESULT_DIFF
                    result.set_cmp_result(single_result)
                result.add_component(data)
        result.add_count_info(count_result)

        return result

    def compare(self):
        compare_list = []
        similar_dumpers = self.get_similar_rpm_pairs(self.dump_base, self.dump_other)
        for single_pair in similar_dumpers:
            if single_pair:
                dump_base, dump_other = single_pair[0], single_pair[1]
                result = self.compare_result(dump_base, dump_other)
                compare_list.append(result)
        return compare_list

    def run(self):
        result = self.compare()
        return result
