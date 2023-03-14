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

    def __init__(self, dump_a, dump_b, config=None):
        super(ListCompareExecutor, self).__init__(dump_a, dump_b, config)
        self.dump_a = dump_a.run()
        self.dump_b = dump_b.run()
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

    def _strict_compare(self, dump_a, dump_b, single_result):
        count_result = {'same': 0, 'more': 0, 'less': 0, 'diff': 0}
        category = dump_a['category'] if dump_a['category'] == dump_b[
            'category'] else CPM_CATEGORY_DIFF
        result = CompareResultComposite(CMP_TYPE_RPM, single_result, dump_a['rpm'], dump_b['rpm'], category)
        flag_v_r_d = self.extract_version_flag(dump_a['rpm'], dump_b['rpm'])
        component_results = self.format_dump(dump_a[self.data], dump_b[self.data], flag_v_r_d)
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

    def _directory_compare(self, dump_a, dump_b, single_result):
        result = CompareResultComposite(CMP_TYPE_DIRECTORY, single_result, self.dump_a['path'], self.dump_b['path'])
        rpm_set_a, rpm_set_b = set(list(dump_a.keys())), set(list(dump_b.keys()))
        # rpm 完全相同集合
        rpm_sames = rpm_set_a & rpm_set_b

        # 去除rpm完全相同项
        rpm_diffs_a, rpm_diffs_b = rpm_set_a - rpm_sames, rpm_set_b - rpm_sames

        # 使用字典保存rpm name 对应的多版本rpm包, key值为rpm name + rpm arch
        one2more_a = self.rpm_n_a_lists(rpm_diffs_a)
        one2more_b = self.rpm_n_a_lists(rpm_diffs_b)
        rpm_levels = self.compare_rpm_level(rpm_sames, one2more_a, one2more_b)
        for rpm_level in rpm_levels:
            attr_a = dump_a.get(rpm_level[0].split(',')[0])
            attr_b = dump_b.get(rpm_level[1].split(',')[0])
            # 可能出现a包有，b包没有情况

            attr = {'source_package_a': attr_a['source_package'] if attr_a else '',
                    'source_package_b': attr_b['source_package'] if attr_b else '',
                    'category': attr_a['category'] if attr_a else attr_b['category']}
            if rpm_level[-1] != CMP_LEVEL_SAME and single_result == CMP_RESULT_SAME:
                result.set_cmp_result(CMP_RESULT_DIFF)
            result.add_component(
                CompareResultComponent(CMP_TYPE_RPM_LEVEL, rpm_level[-1], rpm_level[0], rpm_level[1], attr))
        return result

    def compare_rpm_level(self, rpm_sames, one2more_a, one2more_b):
        compare_list, row = [], []
        for rpm_same in rpm_sames:
            compare_list.append([rpm_same, rpm_same, CMP_LEVEL_SAME])
        for rpm_n in one2more_a.keys():
            if rpm_n in one2more_b.keys():
                rpm_list_a, rpm_list_b = one2more_a[rpm_n], one2more_b[rpm_n]
                # 根据side_b取rpm相似度最高的对进行比较，side_a中未被取走的rpm不在最终结果中显示
                rpm_similar_pairs = self.get_similar_rpm_pairs(rpm_list_a, rpm_list_b)
                if rpm_similar_pairs:
                    for rpm_pair in rpm_similar_pairs:
                        rpm_a, rpm_b = rpm_pair[0], rpm_pair[1]
                        rpm_a_n, rpm_a_v, rpm_a_r, rpm_a_d, _ = RPMProxy.rpm_n_v_r_d_a(rpm_a)
                        rpm_b_n, rpm_b_v, rpm_b_r, rpm_b_d, _ = RPMProxy.rpm_n_v_r_d_a(rpm_b)
                        # eg: custom_build_tool-1.0-17.oe1.oe1.aarch64.rpm
                        if rpm_a_n == rpm_b_n and rpm_a_v == rpm_b_v and rpm_a_r == rpm_b_r and rpm_a_d == rpm_b_d:
                            row = [rpm_a, rpm_b, CMP_LEVEL_SAME]
                        elif rpm_a_n == rpm_b_n and rpm_a_v == rpm_b_v and rpm_a_r == rpm_b_r and rpm_a_d != rpm_b_d:
                            row = [rpm_a, rpm_b, CMP_LEVEL_NEARLY_SAME]
                        elif rpm_a_n == rpm_b_n and rpm_a_v == rpm_b_v and rpm_a_r != rpm_b_r:
                            row = [rpm_a, rpm_b, CMP_LEVEL_BIG_VERSION_SAME]
                        elif rpm_a_n == rpm_b_n and rpm_a_v != rpm_b_v:
                            row = [rpm_a, rpm_b, CMP_LEVEL_VERSION_DIFF]
                        compare_list.append(row)
            else:
                row = [', '.join(one2more_a[rpm_n]), '', CMP_LEVEL_LESS]
                compare_list.append(row)
        for rpm_n in one2more_b.keys():
            if rpm_n not in one2more_a.keys():
                row = ['', ', '.join(one2more_b[rpm_n]), CMP_LEVEL_MORE]
                compare_list.append(row)
        compare_list.sort(key=lambda x: x[2])
        return compare_list

    def compare(self):
        if self.config.get('strict', False):
            compare_list = []
            similar_dumpers = self.get_similar_rpm_pairs(self.dump_a, self.dump_b)
            for single_pair in similar_dumpers:
                if single_pair:
                    # dump_a: single_pair[0], dump_b: single_pair[1]
                    result = self._strict_compare(single_pair[0], single_pair[1], CMP_RESULT_SAME)
                    compare_list.append(result)
            return compare_list
        if self.config.get('only_directory', False):
            dump_a = self.dump_a[self.data]
            dump_b = self.dump_b[self.data]
            return self._directory_compare(dump_a, dump_b, CMP_RESULT_SAME)

    def run(self):
        result = self.compare()
        if not result:
            logger.debug('compare result empty, %s, %s' % (self.dump_a, self.dump_b))
        return result
