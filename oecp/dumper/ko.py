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
# Description: Get the ko module
# **********************************************************************************
"""
import logging
import os


from oecp.dumper.base import AbstractDumper

logger = logging.getLogger('oecp')


class KoDumper(AbstractDumper):
    def __init__(self, repository, cache=None, config=None):
        super(KoDumper, self).__init__(repository, cache, config)
        cache_require_key = 'extract'
        self.cache_dumper = self.get_cache_dumper(cache_require_key)
        self.extract_info = self.cache_dumper.get_extract_info()
        self._component_key = 'ko'
        self.data = "data"

    def dump_ko_mod(self, repository):
        rpm_path = repository['path']
        category = repository['category'].value
        verbose_path = os.path.basename(rpm_path)
        kabi_white_list = self.cache_dumper.get_kabi_white_list()
        rpm_extract_dir = self.extract_info.get(verbose_path)
        rpm_extract_name = rpm_extract_dir.name
        if not rpm_extract_name:
            raise Exception(f"RPM {verbose_path} decompression path not found.")
        ko_files = self.cache_dumper.get_ko_files(rpm_extract_name)
        item = {
            'rpm': verbose_path,
            'category': category,
            'kind': self._component_key,
            'data': ko_files,
            "white_list": kabi_white_list
        }

        return item, ko_files

    def run(self):
        dumper_list = []
        for repository in self.repository.values():
            dumper, ko_files = self.dump_ko_mod(repository)
            if not dumper_list:
                dumper_list.append(dumper)
            elif ko_files:
                for item in dumper_list:
                    if not item.get('data', []):
                        dumper_list.remove(item)
                dumper_list.append(dumper)

        return dumper_list
