# -*- encoding=utf-8 -*-
"""
# **********************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2021-2021. All rights reserved.
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

import json
import logging
import os.path

from oecp.result.compress import gen_hash_key
from oecp.result.constants import TOOLS_RESULT_ITEMS, PLATFORM_RESULT_ITEMS

logger = logging.getLogger("oecp")


class WebShowResult:
    def __init__(self, tools_result, conclusion):
        self.web_show_result = {}
        self.tools_result = tools_result
        self.conclusion = conclusion

    def to_a_percentage(self, date):
        percent_data = format(round(date, 4), '.2%')
        return percent_data

    def get_exists_item(self, similarity, items):
        items_result = []
        for item in items:
            for single_check_result in similarity.keys():
                if single_check_result == item:
                    items_result.append(item)
        return items_result

    def get_tools_result(self, namelist, similarity, tools_result):
        tools_result_data = []
        for single_result in namelist:
            result_details = {}
            if single_result == 'level2 pkg':
                result_details.setdefault("name", 'soft_pkg')
            elif single_result == 'kabi':
                result_details.setdefault("name", 'KABI')
            elif single_result == 'level2 rpm abi':
                result_details.setdefault("name", 'ABI')
            elif single_result == 'service detail':
                result_details.setdefault("name", 'service_config')
            elif single_result == 'rpm config':
                result_details.setdefault("name", 'soft_config')
            elif single_result == 'kconfig':
                result_details.setdefault("name", 'kernel_config')
            else:
                result_details.setdefault("name", single_result)
            result_details.setdefault("percent", self.to_a_percentage(similarity[single_result]))
            result_details.setdefault("result", tools_result[single_result])
            tools_result_data.append(result_details)
        return tools_result_data

    def get_platform_result(self, namelist, similarity, tools_result):
        platform_result_data = []
        for single_result in namelist:
            result_details = {}
            if single_result == 'rpm test':
                result_details.setdefault("name", 'repo')
            elif single_result == 'AT':
                result_details.setdefault("name", 'base_test')
            elif single_result == 'performance':
                result_details.setdefault("name", 'performance_test')
            elif single_result == 'ciconfig':
                result_details.setdefault("name", 'running_config')
            result_details.setdefault("percent", self.to_a_percentage(similarity[single_result]))
            result_details.setdefault("result", tools_result[single_result])
            platform_result_data.append(result_details)
        return platform_result_data

    def create_report_json(self, root_path, osv_title):
        floder_path = os.path.join(root_path, osv_title)
        if not floder_path:
            os.makedirs(floder_path)
        file_path = os.path.join(floder_path, 'web_show_result.json').replace("\\", '/')
        json_result = json.dumps(self.web_show_result)
        with open(file_path, 'w') as rf:
            rf.write(json_result)

    def write_json_result(self, *args):
        try:
            similarity, side_a, side_b, root_path, osv_title, iso_path = args
            self.web_show_result.setdefault('osv_name', side_b.split('-')[0])
            conclusion = 'PASS' if self.conclusion == '通过' else 'NO PASS'
            self.web_show_result.setdefault('total_result', conclusion)
            arch = "aarch64" if "aarch64" in side_b else "X86"
            self.web_show_result.setdefault('arch', arch)
            self.web_show_result.setdefault('os_download_link', '')
            checksum = gen_hash_key(iso_path)
            self.web_show_result.setdefault('checksum', checksum)
            self.web_show_result.setdefault('base_openeuler_version', ' '.join(side_a.split('-')[:3]))
            tools_result_item = self.get_exists_item(similarity, TOOLS_RESULT_ITEMS)
            platform_result_item = self.get_exists_item(similarity, PLATFORM_RESULT_ITEMS)
            if tools_result_item and platform_result_item:
                tools_result_data = self.get_tools_result(tools_result_item, similarity, self.tools_result)
                platform_result_data = self.get_platform_result(platform_result_item, similarity, self.tools_result)
                self.web_show_result.setdefault('tools_result', tools_result_data)
                self.web_show_result.setdefault('platform_result', platform_result_data)
                self.create_report_json(root_path, osv_title)
            else:
                logger.warning('The items displayed in the JSON report is empty.')
        except(AttributeError, KeyError, OSError, ValueError):
            logger.exception("json statistics error")
