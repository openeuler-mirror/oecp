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

from oecp.dumper.base import AbstractDumper
from oecp.proxy.rpm_proxy import RPMProxy
from oecp.result.constants import CMP_TYPE_KO

logger = logging.getLogger('oecp')


class KoDumper(AbstractDumper):
    def __init__(self, repository, cache=None, config=None):
        super(KoDumper, self).__init__(repository, cache, config)

    def dump_ko_mod(self, repository):
        category = repository['category'].value
        src_rpm = RPMProxy.rpm_name(repository['src'])
        if self.cmp_model:
            verbose_path = repository.get('rpm_name')
            ko_files = [repository.get('path')]
        else:
            verbose_path = repository['verbose_path']
            cache_dumper = self.get_cache_dumper(self.cache_require_key)
            extract_info = cache_dumper.get_extract_info()
            rpm_extract_name = extract_info.get(verbose_path).name
            if not rpm_extract_name:
                raise ValueError("RPM %s decompression path not found.", verbose_path)
            ko_files = cache_dumper.get_ko_files(rpm_extract_name)
        self.load_white_list(verbose_path)
        item = {
            'rpm': verbose_path,
            'category': category,
            'src_name': src_rpm,
            'kind': CMP_TYPE_KO,
            self.data: ko_files,
            'white_list': self.kabi_white_list
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
                    if not item.get(self.data, []):
                        dumper_list.remove(item)
                dumper_list.append(dumper)

        return dumper_list
