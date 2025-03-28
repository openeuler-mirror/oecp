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
# Author:
# Create: 2023-07-25
# Description: Compare the ko module.
# **********************************************************************************
"""

import logging
import os
import re
import uuid
import yaml

from oecp.executor.base import CompareExecutor
from oecp.result.compare_result import CompareResultComposite, CompareResultComponent
from oecp.result.constants import CMP_RESULT_SAME, CMP_TYPE_RPM, CMP_RESULT_DIFF, CMP_RESULT_LESS, CMP_TYPE_KO_INFO, \
    CMP_TYPE_KO, DETAIL_PATH
from oecp.utils.shell import shell_cmd

logger = logging.getLogger('oecp')


class KoCompareExecutor(CompareExecutor):

    def __init__(self, base_dump, other_dump, config=None):
        super(KoCompareExecutor, self).__init__(base_dump, other_dump, config)
        self.base_dump = base_dump.run()
        self.other_dump = other_dump.run()
        self.data = 'data'
        self.ko_flag = '_ko_'

    @staticmethod
    def parse_ko_abi_info(ko_path, ko_info):
        cmd = ["modprobe", "--dump-modversions", ko_path]
        ret, out, err = shell_cmd(cmd)
        if not ret:
            if err:
                logger.warning(err)
            if out:
                for line in out.split('\n'):
                    if not line:
                        continue
                    crc, symbol = line.split()
                    ko_info.setdefault("ko symbol:  " + symbol, crc)

    @staticmethod
    def get_whitelist_rpms():
        whitelist = []
        whitelist_rpms_path = os.path.realpath(
            os.path.join(os.path.dirname(__file__), '../conf/ko_whitelist_rpms.yaml'))
        try:
            with open(whitelist_rpms_path, "r") as f:
                whitelist = yaml.safe_load(f)
        except FileNotFoundError as err:
            logger.error("Not found path of ko whitelist rpms, %s", err)

        return whitelist

    def _set_ko_info_details(self, result, component_dump, cmp_type, cmp_result=CMP_RESULT_SAME):
        whitelist_rpms = self.get_whitelist_rpms()
        for component_result in component_dump:
            for sub_component_result in component_result:
                single_info = sub_component_result[0] if sub_component_result[0] else sub_component_result[1]
                in_white_list = "uninvolved"
                if re.match("ko symbol", single_info):
                    kabi = single_info.split()[-2]
                    if self.kabi_white_list:
                        in_white_list = "Yes" if kabi in self.kabi_white_list else "No"
                data = CompareResultComponent(CMP_TYPE_KO_INFO, sub_component_result[-1], sub_component_result[0],
                                              sub_component_result[1], in_white_list)
                if cmp_result == CMP_RESULT_SAME:
                    if sub_component_result[-1] != CMP_RESULT_SAME and not single_info.startswith('srcversion'):
                        cmp_result = CMP_RESULT_DIFF
                        result.set_cmp_result(cmp_result)
                    elif in_white_list == "No" and self.src_name in whitelist_rpms:
                        cmp_result = CMP_RESULT_DIFF
                        result.set_cmp_result(cmp_result)
                result.add_component(data)

        return cmp_result if cmp_type == CMP_RESULT_SAME else cmp_type

    def parse_ko_info(self, ko_path):
        if not os.path.exists(ko_path):
            return None

        ko_info = {
            "license:": "",
            "srcversion:": "",
            "depends:": "",
            "vermagic:": ""
        }
        cmd = ['modinfo', ko_path]
        ret, out, err = shell_cmd(cmd)
        if not ret:
            if err:
                logger.warning(err)
            if out:
                for item in ko_info.keys():
                    item_pattern = re.compile(item + r"(.*)\n")
                    item_result = re.search(item_pattern, out)
                    if not item_result:
                        continue
                    item_info = item_result.group(1)
                    ko_info[item] = item_info.strip()
                alias_match = re.findall(r"alias:\s+(\S+)\n", out)
                ko_info.setdefault("alias:", alias_match)
        self.parse_ko_abi_info(ko_path, ko_info)

        return ko_info

    def _compare_result(self, base_dump, other_dump, cmp_result=CMP_RESULT_SAME):
        count_result = {'same': 0, 'more': 0, 'less': 0, 'diff': 0}
        category = base_dump['category']
        kind = base_dump['kind']
        self.src_name = base_dump['src_name']
        self.kabi_white_list = base_dump["white_list"] if base_dump.get("white_list") else other_dump.get("white_list")
        result = CompareResultComposite(CMP_TYPE_RPM, cmp_result, base_dump['rpm'], other_dump['rpm'], category)
        base_map_ko = self.split_files_mapping(base_dump[self.data], CMP_TYPE_KO)
        other_map_ko = self.split_files_mapping(other_dump[self.data], CMP_TYPE_KO)
        if not base_map_ko and not other_map_ko:
            logger.debug("No %s modules found!", kind)
            return result
        format_results = self.format_ko_files(base_map_ko, other_map_ko)
        for cmp_type, pairs in format_results.items():
            for pair in pairs:
                base_ko = pair[0].split(self.split_flag)[-1] if pair[0] else ''
                other_ko = pair[1].split(self.split_flag)[-1] if pair[1] else ''
                base_ko_info = self.parse_ko_info(pair[0])
                other_ko_info = self.parse_ko_info(pair[1])
                base_ko_name, other_ko_name = os.path.basename(base_ko), os.path.basename(other_ko)
                ko_uid = self.ko_flag.join(
                    [other_ko_name if other_ko_name else base_ko_name, str(uuid.uuid4().clock_seq)])

                if base_ko_name and other_ko_name:
                    ko_detail_name = "%s_vs_%s.csv" % (base_ko_name, ko_uid)
                else:
                    ko_detail_name = "%s.csv" % ko_uid
                details_path = os.path.join(DETAIL_PATH, 'ko_info', ko_detail_name)
                component_dump = self.format_ko_info(base_ko_info, other_ko_info)
                detail_result = CompareResultComposite(CMP_TYPE_KO_INFO, CMP_RESULT_SAME, base_ko_name, ko_uid,
                                                       ko_detail_name)
                cmp_result = self._set_ko_info_details(detail_result, component_dump, cmp_type)
                self.count_cmp_result(count_result, cmp_result)
                data = CompareResultComponent(CMP_TYPE_KO, cmp_result, base_ko, other_ko, details_path)
                if cmp_result in [CMP_RESULT_DIFF, CMP_RESULT_LESS]:
                    result.set_cmp_result(CMP_RESULT_DIFF)
                result.add_component(data)
                result.add_component(detail_result)

        result.add_count_info(count_result)

        return result

    def compare(self):
        compare_list = []
        similar_dumpers = self.get_similar_rpm_pairs(self.base_dump, self.other_dump)
        for single_pair in similar_dumpers:
            if single_pair:
                base_dump, other_dump = single_pair[0], single_pair[1]
                result = self._compare_result(base_dump, other_dump)
                compare_list.append(result)
        return compare_list

    def run(self):
        result = self.compare()
        return result
