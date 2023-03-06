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

from oecp.executor.base import CompareExecutor
from oecp.result.compare_result import CMP_RESULT_SAME, CompareResultComposite, CMP_TYPE_RPM, CMP_RESULT_DIFF, \
    CompareResultComponent, CMP_TYPE_SERVICE, CMP_TYPE_SERVICE_DETAIL, CMP_RESULT_LESS, CMP_RESULT_MORE, DETAIL_PATH

logger = logging.getLogger('oecp')


class ServiceCompareExecutor(CompareExecutor):

    def __init__(self, dump_a, dump_b, config=None):
        super(ServiceCompareExecutor, self).__init__(dump_a, dump_b, config)
        self.dump_a = dump_a.run()
        self.dump_b = dump_b.run()
        self.data = 'data'

    @staticmethod
    def _load_details(file_path):
        """
        set service file as dict
        :param file_path:servie file path
        :return:
        """
        item = {}
        with open(file_path, "r") as f:
            for line in f.readlines():
                line = line.strip().replace("\n", "")
                if line == "":
                    continue
                if line.startswith("#"):
                    continue
                if '=' in line:
                    name, version = line.split("=", 1)
                    # 一个service文件中出现相同key情况下，原值进行拼接处理
                    if name in item.keys():
                        version = item[name] + '||SAMEKEY||' + version
                    item.setdefault(name, version)
        return item

    @staticmethod
    def _detail_set(dump_a, dump_b, component_results, detail_filename, single_result=CMP_RESULT_SAME):
        """
        格式化比较文件结果并输出对比结果
        :param component_results:side_a and side_b service 文件的对比结果
        :return:
        """
        result = CompareResultComposite(CMP_TYPE_SERVICE_DETAIL, single_result, dump_a['rpm'], dump_b['rpm'])
        for component_result in component_results:
            for sub_component_result in component_result:
                data = CompareResultComponent(CMP_TYPE_SERVICE_DETAIL, sub_component_result[-1],
                                              sub_component_result[0], sub_component_result[1])
                if sub_component_result[-1] != CMP_RESULT_SAME and single_result == CMP_RESULT_SAME:
                    single_result = CMP_RESULT_DIFF
                    result.set_cmp_result(single_result)
                result.detail = {"file_name": detail_filename}
                result.add_component(data)
        return result

    def _compare_result(self, dump_a, dump_b, single_result=CMP_RESULT_SAME):
        count_result = {'same': 0, 'more': 0, 'less': 0, 'diff': 0}
        category = dump_a['category']
        flag_v_r_d = self.extract_version_flag(dump_a['rpm'], dump_b['rpm'])
        result = CompareResultComposite(CMP_TYPE_RPM, single_result, dump_a['rpm'], dump_b['rpm'], category)
        dump_a_files = self.split_files_mapping(dump_a[self.data])
        dump_b_files = self.split_files_mapping(dump_b[self.data])
        common_file_pairs, only_file_a, only_file_b = self.format_fullpath_files(dump_a_files, dump_b_files, flag_v_r_d)
        if not common_file_pairs and not only_file_a and not only_file_b:
            logger.debug(f"No service package found, ignored with {dump_b['rpm']} and {dump_b['rpm']}")
            return result
        details_path = os.path.join(DETAIL_PATH, 'service-detail', dump_b['rpm']) + '.csv'
        for pair in common_file_pairs:
            base_a = pair[0].split(self.split_flag)[-1]
            base_b = pair[1].split(self.split_flag)[-1]
            details_a = self._load_details(pair[0])
            details_b = self._load_details(pair[1])
            file_result, component_results = self.format_service_detail(details_a, details_b)
            if file_result == CMP_RESULT_DIFF:
                self.count_cmp_result(count_result, CMP_RESULT_DIFF)
                data = CompareResultComponent(CMP_TYPE_SERVICE, file_result, base_a, base_b, details_path)
                result.set_cmp_result(file_result)
            else:
                self.count_cmp_result(count_result, file_result)
                data = CompareResultComponent(CMP_TYPE_SERVICE, file_result, base_a, base_b)
            result.add_component(data)
            result_detail = self._detail_set(dump_a, dump_b, component_results, base_a)
            result.add_component(result_detail)

        for file_a in only_file_a:
            self.count_cmp_result(count_result, CMP_RESULT_LESS)
            data = CompareResultComponent(CMP_TYPE_SERVICE, CMP_RESULT_LESS, file_a, '')
            result.add_component(data)

        for file_b in only_file_b:
            self.count_cmp_result(count_result, CMP_RESULT_MORE)
            data = CompareResultComponent(CMP_TYPE_SERVICE, CMP_RESULT_MORE, '', file_b)
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
