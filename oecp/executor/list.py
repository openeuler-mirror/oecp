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
from oecp.executor.base import CompareExecutor, CPM_CATEGORY_DIFF
from oecp.result.compare_result import CompareResultComposite, CMP_TYPE_RPM, CompareResultComponent, \
    CMP_TYPE_DIRECTORY, CMP_TYPE_RPM_LEVEL, CMP_RESULT_SAME, CMP_RESULT_DIFF
from oecp.proxy.rpm_proxy import RPMProxy
from oecp.result.constants import CMP_SAME_RESULT

logger = logging.getLogger('oecp')

# rpm compare level

CMP_LEVEL_SAME = '1'
CMP_LEVEL_NEARLY_SAME = '1.1'
CMP_LEVEL_BIG_VERSION_SAME = '2'
CMP_LEVEL_VERSION_DIFF = '3'
CMP_LEVEL_LESS = '4'
CMP_LEVEL_MORE = '5'


class ListCompareExecutor(CompareExecutor):

    def __init__(self, base_dump, other_dump, config=None):
        super(ListCompareExecutor, self).__init__(base_dump, other_dump, config)
        self.base_dump = base_dump.run()
        self.other_dump = other_dump.run()
        self.config = config if config else {}
        self.data = 'data'

    @staticmethod
    def rpm_n_a_lists(rpm_diffs):
        one2more = {}
        for rpm_a in sorted(rpm_diffs):
            r_n, _, _, _, r_a = RPMProxy.rpm_n_v_r_d_a(rpm_a)
            rpm_n_a = r_n + '$' + r_a
            one2more.setdefault(rpm_n_a, []).append(rpm_a)
        return one2more

    @staticmethod
    def cmp_rpms_similarity(similar_pairs, compare_list, row):
        for rpm_pair in similar_pairs:
            base_rpm, other_rpm = rpm_pair[0], rpm_pair[1]
            base_rpm_name, base_rpm_version, base_rpm_release, base_rpm_dist, _ = RPMProxy.rpm_n_v_r_d_a(base_rpm)
            other_rpm_name, other_rpm_version, other_rpm_release, other_rpm_dist, _ = RPMProxy.rpm_n_v_r_d_a(other_rpm)
            # eg: custom_build_tool-1.0-17.oe1.oe1.aarch64.rpm
            if base_rpm_name == other_rpm_name and base_rpm_version == other_rpm_version and base_rpm_release == \
                    other_rpm_release and base_rpm_dist == other_rpm_dist:
                row = [base_rpm, other_rpm, CMP_LEVEL_SAME]
            elif base_rpm_name == other_rpm_name and base_rpm_version == other_rpm_version and base_rpm_release == \
                    other_rpm_release and base_rpm_dist != other_rpm_dist:
                row = [base_rpm, other_rpm, CMP_LEVEL_NEARLY_SAME]
            elif base_rpm_name == other_rpm_name and base_rpm_version == other_rpm_version and base_rpm_release != \
                    other_rpm_release:
                row = [base_rpm, other_rpm, CMP_LEVEL_BIG_VERSION_SAME]
            elif base_rpm_name == other_rpm_name and base_rpm_version != other_rpm_version:
                row = [base_rpm, other_rpm, CMP_LEVEL_VERSION_DIFF]
            compare_list.append(row)

    def strict_compare(self, base_dump, other_dump, single_result):
        count_result = {'same': 0, 'more': 0, 'less': 0, 'diff': 0}
        category = base_dump['category'] if base_dump['category'] == other_dump['category'] else CPM_CATEGORY_DIFF
        result = CompareResultComposite(CMP_TYPE_RPM, single_result, base_dump['rpm'], other_dump['rpm'], category)
        flag_v_r_d = self.extract_version_flag(base_dump['rpm'], other_dump['rpm'])
        component_results = self.format_dump(base_dump[self.data], other_dump[self.data], flag_v_r_d)
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

    def directory_compare(self, base_dump, other_dump, single_result):
        result = CompareResultComposite(CMP_TYPE_DIRECTORY, single_result, self.base_dump['path'],
                                        self.other_dump['path'])
        # rpm 完全相同集合
        rpm_sames = set(base_dump.keys()) & set(other_dump.keys())
        # 去除rpm完全相同项
        rpm_diffs_in_base, rpm_diffs_in_other = set(base_dump.keys()) - rpm_sames, set(other_dump.keys()) - rpm_sames

        # 使用字典保存rpm name 对应的多版本rpm包, key值为rpm name + rpm arch
        one2more_base = self.rpm_n_a_lists(rpm_diffs_in_base)
        one2more_other = self.rpm_n_a_lists(rpm_diffs_in_other)
        rpm_levels = self.compare_rpm_level(rpm_sames, one2more_base, one2more_other)
        for rpm_level in rpm_levels:
            attr_base = base_dump.get(rpm_level[0].split(',')[0])
            attr_other = other_dump.get(rpm_level[1].split(',')[0])
            # 可能出现base包有，other包没有情况

            attr = {'source_package_a': attr_base['source_package'] if attr_base else '',
                    'source_package_b': attr_other['source_package'] if attr_other else '',
                    'category': attr_base['category'] if attr_base else attr_other['category']}
            if rpm_level[-1] != CMP_LEVEL_SAME and single_result == CMP_RESULT_SAME:
                result.set_cmp_result(CMP_RESULT_DIFF)
            result.add_component(
                CompareResultComponent(CMP_TYPE_RPM_LEVEL, rpm_level[-1], rpm_level[0], rpm_level[1], attr))
        return result

    def compare_rpm_level(self, rpm_sames, one2more_base, one2more_other):
        compare_list, row = [], []
        for rpm_same in rpm_sames:
            compare_list.append([rpm_same, rpm_same, CMP_LEVEL_SAME])
        for rpm_name in one2more_base.keys():
            if rpm_name in one2more_other.keys():
                rpm_list_base, rpm_list_other = one2more_base[rpm_name], one2more_other[rpm_name]
                # 根据side_b取rpm相似度最高的对进行比较，side_a中未被取走的rpm不在最终结果中显示
                rpm_similar_pairs = self.get_similar_rpm_pairs(rpm_list_base, rpm_list_other)
                self.cmp_rpms_similarity(rpm_similar_pairs, compare_list, row)
            else:
                row = [', '.join(one2more_base[rpm_name]), '', CMP_LEVEL_LESS]
                compare_list.append(row)
        for rpm_name in one2more_other.keys():
            if rpm_name not in one2more_base.keys():
                row = ['', ', '.join(one2more_other[rpm_name]), CMP_LEVEL_MORE]
                compare_list.append(row)
        compare_list.sort(key=lambda x: x[2])
        return compare_list

    def compare(self):
        if self.config.get('strict', False):
            compare_list = []
            similar_dumpers = self.get_similar_rpm_pairs(self.base_dump, self.other_dump)
            for single_pair in similar_dumpers:
                if single_pair:
                    # dump_base: single_pair[0], dump_other: single_pair[1]
                    result = self.strict_compare(single_pair[0], single_pair[1], CMP_RESULT_SAME)
                    compare_list.append(result)
            return compare_list
        if self.config.get('only_directory', False):
            base_dump = self.base_dump[self.data]
            other_dump = self.other_dump[self.data]
            return self.directory_compare(base_dump, other_dump, CMP_RESULT_SAME)

    def run(self):
        result = self.compare()
        if not result:
            logger.debug('compare result empty, %s, %s', self.base_dump, self.other_dump)
        return result
