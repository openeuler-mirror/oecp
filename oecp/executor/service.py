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
from oecp.result.compare_result import CompareResultComposite, CompareResultComponent
from oecp.result.constants import CMP_SERVICE_SAME, CMP_RESULT_SAME, CMP_TYPE_RPM, CMP_RESULT_DIFF, CMP_TYPE_SERVICE, \
    CMP_TYPE_SERVICE_DETAIL, CMP_RESULT_LESS, CMP_RESULT_MORE, DETAIL_PATH

logger = logging.getLogger('oecp')


class ServiceCompareExecutor(CompareExecutor):

    def __init__(self, base_dump, other_dump, config=None):
        super(ServiceCompareExecutor, self).__init__(base_dump, other_dump, config)
        self.base_dump = base_dump.run()
        self.other_dump = other_dump.run()
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
    def _detail_set(base_dump, other_dump, component_results, detail_filename, single_result=CMP_RESULT_SAME):
        """
        格式化比较文件结果并输出对比结果
        :param component_results:base_side and other_side service 文件的对比结果
        :return:
        """
        result = CompareResultComposite(CMP_TYPE_SERVICE_DETAIL, single_result, base_dump['rpm'], other_dump['rpm'])
        for component_result in component_results:
            for sub_component_result in component_result:
                data = CompareResultComponent(CMP_TYPE_SERVICE_DETAIL, sub_component_result[-1],
                                              sub_component_result[0], sub_component_result[1])
                if sub_component_result[-1] not in CMP_SERVICE_SAME and single_result == CMP_RESULT_SAME:
                    single_result = CMP_RESULT_DIFF
                    result.set_cmp_result(single_result)
                result.detail = {"file_name": detail_filename}
                result.add_component(data)
        return result

    def compare_result(self, base_dump, other_dump, single_result=CMP_RESULT_SAME):
        count_result = {'same': 0, 'more': 0, 'less': 0, 'diff': 0}
        category = base_dump['category']
        result = CompareResultComposite(CMP_TYPE_RPM, single_result, base_dump['rpm'], other_dump['rpm'], category)
        base_files, other_files = base_dump[self.data], other_dump[self.data]
        if base_dump.get('model'):
            common_file_pairs = zip(base_files, other_files)
            less_dumps, more_dumps = [], []
        else:
            flag_vrd = self.extract_version_flag(base_dump['rpm'], other_dump['rpm'])
            common_file_pairs, less_dumps, more_dumps = self.format_fullpath_files(base_files, other_files, flag_vrd)
        if not common_file_pairs and not less_dumps and not more_dumps:
            logger.debug(f"No service package found, ignored with {other_dump['rpm']} and {other_dump['rpm']}")
            return result
        details_path = os.path.join(DETAIL_PATH, 'service-detail', other_dump['rpm']) + '.csv'
        for pair in common_file_pairs:
            base_service = pair[0].split(self.split_flag)[-1]
            other_service = pair[1].split(self.split_flag)[-1]
            base_details = self._load_details(pair[0])
            other_details = self._load_details(pair[1])
            file_result, component_results = self.format_service_detail(base_details, other_details)
            if file_result == CMP_RESULT_DIFF:
                self.count_cmp_result(count_result, CMP_RESULT_DIFF)
                data = CompareResultComponent(CMP_TYPE_SERVICE, file_result, base_service, other_service, details_path)
                result.set_cmp_result(file_result)
            else:
                self.count_cmp_result(count_result, file_result)
                data = CompareResultComponent(CMP_TYPE_SERVICE, file_result, base_service, other_service, details_path)
            result.add_component(data)
            result_detail = self._detail_set(base_dump, other_dump, component_results, base_service)
            result.add_component(result_detail)

        for base_file in less_dumps:
            self.count_cmp_result(count_result, CMP_RESULT_LESS)
            data = CompareResultComponent(CMP_TYPE_SERVICE, CMP_RESULT_LESS, base_file, '')
            result.add_component(data)

        for other_file in more_dumps:
            self.count_cmp_result(count_result, CMP_RESULT_MORE)
            data = CompareResultComponent(CMP_TYPE_SERVICE, CMP_RESULT_MORE, '', other_file)
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
