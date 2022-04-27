# -*- encoding=utf-8 -*-
"""
# **********************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# [oecp] is licensed under the Mulan PSL v1.
# You can use this software according to the terms and conditions of the Mulan PSL v1.
# You may obtain a copy of Mulan PSL v1 at:
#     http://license.coscl.org.cn/MulanPSL
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v1 for more details.
# **********************************************************************************
"""

import logging
import os

from oecp.executor.base import CompareExecutor
from oecp.result.compare_result import CMP_RESULT_SAME, CompareResultComposite, CMP_TYPE_RPM, CMP_RESULT_DIFF, \
    CompareResultComponent, CMP_TYPE_SERVICE,CMP_TYPE_SERVICE_DETAIL, CMP_RESULT_LESS, CMP_RESULT_MORE
from oecp.proxy.rpm_proxy import RPMProxy

logger = logging.getLogger('oecp')

class ServiceCompareExecutor(CompareExecutor):

    def __init__(self, dump_a, dump_b, config=None):
        super(ServiceCompareExecutor, self).__init__(dump_a, dump_b, config)
        self.dump_a = dump_a.run()
        self.dump_b = dump_b.run()
        cache_require_key = 'extract'
        self._work_dir = self.config.get(cache_require_key, {}).get('work_dir', '/tmp/oecp')
        self.data = 'data'
        self.split_flag = '__rpm__'

    def _split_common_files(self, files_a, files_b):
        """
        split rpm service file to service pair
        :param files_a:all rpm_a sevice files
        :param files_b:all rpm_b sevice files
        :return:
        """
        common_file_pairs = []
        for file_a in files_a:
            for file_b in files_b:
                if file_a.split(self.split_flag)[-1] == file_b.split(self.split_flag)[-1]:
                    common_file_pairs.append([file_a, file_b])
        return common_file_pairs

    def _intercept_file_name(self, file, pattern="full"):
        common_path_flag = '/usr/lib/systemd/system/'
        full_path = file.split(self.split_flag)[-1]
        if pattern == 'half':
            half_path = full_path.split(common_path_flag)[-1]
            if '/' in half_path:
                half_path = '/' + half_path
            return half_path
        return full_path

    def _load_details(self,file_path):
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
                    item.setdefault(name,version)
        return item

    def _detail_set(self, dump_a, dump_b, component_results, detail_filename, single_result=CMP_RESULT_SAME):
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
                result._detail = {"file_name": detail_filename}
                result.add_component(data)
        return result

    def _compare_result(self, dump_a, dump_b, single_result=CMP_RESULT_SAME):
        count_result = {'more_count': 0, 'less_count': 0, 'diff_count': 0}
        category = dump_a['category']
        result = CompareResultComposite(CMP_TYPE_RPM, single_result, dump_a['rpm'], dump_b['rpm'], category)
        dump_a_files = dump_a[self.data]
        dump_b_files = dump_b[self.data]
        common_file_pairs, only_file_a, only_file_b = self.split_common_files(dump_a_files, dump_b_files)
        if not common_file_pairs:
            logger.debug(f"No service package found, ignored with {dump_b['rpm']} and {dump_b['rpm']}")
            return result
        for pair in common_file_pairs:
            detail_filename = self._intercept_file_name(pair[0])
            # 不显示/usr/lib/systemd/system/路径
            base_a = self._intercept_file_name(pair[0], 'half')
            base_b = self._intercept_file_name(pair[1], 'half')
            details_a = self._load_details(pair[0])
            details_b = self._load_details(pair[1])
            file_result, component_results = self.format_service_detail(details_a, details_b)
            if file_result == 'diff':
                count_result["diff_count"] += 1
                result.set_cmp_result(file_result)
            data = CompareResultComponent(
                CMP_TYPE_SERVICE, file_result, base_a, base_b)
            result.add_component(data)
            result_detail = self._detail_set(dump_a, dump_b, component_results, detail_filename)
            result.add_component(result_detail)
        if only_file_a:
            for file_a in only_file_a:
                side_a = self._intercept_file_name(file_a, 'half')
                data = CompareResultComponent(CMP_TYPE_SERVICE, CMP_RESULT_LESS, side_a, '')
                result.add_component(data)
                count_result["less_count"] += 1
        if only_file_b:
            for file_b in only_file_b:
                side_b = self._intercept_file_name(file_b, 'half')
                data = CompareResultComponent(CMP_TYPE_SERVICE, CMP_RESULT_MORE, '', side_b)
                result.add_component(data)
                count_result["more_count"] += 1
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

