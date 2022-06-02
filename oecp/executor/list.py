# -*- encoding=utf-8 -*-
"""
# **********************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# [oecp] is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# **********************************************************************************
"""

import logging
from oecp.executor.base import CompareExecutor, CPM_CATEGORY_DIFF
from oecp.result.compare_result import CompareResultComposite, CMP_TYPE_RPM, CompareResultComponent, CMP_TYPE_DIRECTORY, \
    CMP_TYPE_RPM_LEVEL, CMP_RESULT_SAME, CMP_RESULT_DIFF, CMP_RESULT_EXCEPTION
from oecp.proxy.rpm_proxy import RPMProxy
from oecp.result.constants import CMP_RESULT_CHANGE

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

    def _strict_compare(self, dump_a, dump_b, single_result=CMP_RESULT_SAME):
        count_result = {'more_count': 0, 'less_count': 0, 'diff_count': 0}
        category = dump_a['category'] if dump_a['category'] == dump_b[
            'category'] else CPM_CATEGORY_DIFF
        result = CompareResultComposite(CMP_TYPE_RPM, single_result, dump_a['rpm'], dump_b['rpm'], category)
        component_results = self.format_dump(dump_a[self.data], dump_b[self.data])
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

    def _directory_compare(self, dump_a, dump_b, single_result=CMP_RESULT_SAME):
        result = CompareResultComposite(CMP_TYPE_DIRECTORY, single_result, self.dump_a['path'], self.dump_b['path'])
        rpm_set_a, rpm_set_b = set(list(dump_a.keys())), set(list(dump_b.keys()))
        # rpm 完全相同集合
        rpm_sames = rpm_set_a & rpm_set_b

        # 去除rpm完全相同项
        rpm_diffs_a, rpm_diffs_b = rpm_set_a - rpm_sames, rpm_set_b - rpm_sames

        # 使用字典保存rpm name 对应的多版本rpm包
        one2more_a, one2more_b = {}, {}
        for rpm_a in rpm_diffs_a:
            one2more_a.setdefault(RPMProxy.rpm_n_v_r_d_a(rpm_a)[0], []).append(rpm_a)
        for rpm_b in rpm_diffs_b:
            one2more_b.setdefault(RPMProxy.rpm_n_v_r_d_a(rpm_b)[0], []).append(rpm_b)
        rpm_levels = self._compare_rpm_level(rpm_sames, one2more_a, one2more_b)
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

    @staticmethod
    def _compare_rpm_level(rpm_sames, one2more_a, one2more_b):
        compare_list = []
        for rpm_same in rpm_sames:
            compare_list.append([rpm_same, rpm_same, CMP_LEVEL_SAME])
        for rpm_n in one2more_a.keys():
            if rpm_n in one2more_b.keys():
                rpm_list_a, rpm_list_b = one2more_a[rpm_n], one2more_b[rpm_n]
                rpm_list_a.sort()
                rpm_list_b.sort()
                rpm_a, rpm_b = ', '.join(rpm_list_a), ', '.join(rpm_list_b)
                # 多版本rpm排序后，取第一个版本进行比较
                rpm_a_n, rpm_a_v, rpm_a_r, rpm_a_d, _ = RPMProxy.rpm_n_v_r_d_a(rpm_list_a[0])
                rpm_b_n, rpm_b_v, rpm_b_r, rpm_b_d, _ = RPMProxy.rpm_n_v_r_d_a(rpm_list_b[0])
                if rpm_a_n == rpm_b_n and rpm_a_v == rpm_b_v and rpm_a_r == rpm_b_r and rpm_a_d != rpm_b_d:
                    row = [rpm_a, rpm_b, CMP_LEVEL_NEARLY_SAME]
                elif rpm_a_n == rpm_b_n and rpm_a_v == rpm_b_v and rpm_a_r != rpm_b_r:
                    row = [rpm_a, rpm_b, CMP_LEVEL_BIG_VERSION_SAME]
                elif rpm_a_n == rpm_b_n and rpm_a_v != rpm_b_v:
                    row = [rpm_a, rpm_b, CMP_LEVEL_VERSION_DIFF]
                else:
                    logger.warning(f'unknown level for {rpm_a} {rpm_b}')
                    row = [rpm_a, rpm_b, CMP_RESULT_EXCEPTION]
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
            for dump_a in self.dump_a:
                for dump_b in self.dump_b:
                    # 取rpm name 相同进行比较
                    if RPMProxy.rpm_name(dump_a['rpm']) == RPMProxy.rpm_name(dump_b['rpm']):
                        result = self._strict_compare(dump_a, dump_b)
                        compare_list.append(result)
            return compare_list
        if self.config.get('only_directory', False):
            dump_a = self.dump_a[self.data]
            dump_b = self.dump_b[self.data]
            return self._directory_compare(dump_a, dump_b)

    def run(self):
        result = self.compare()
        if not result:
            logger.debug('compare result empty, %s, %s' % (self.dump_a, self.dump_b))
        return result
