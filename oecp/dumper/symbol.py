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

import os
import logging

logger = logging.getLogger('oecp')

from oecp.dumper.base import AbstractDumper


class SymbolDumper(AbstractDumper):
    def __init__(self, repository, cache=None, config=None):
        super(SymbolDumper, self).__init__(repository, cache, config)
        cache_require_key = 'extract'
        self.cache_dumper = self.get_cache_dumper(cache_require_key)
        self.extract_info = self.cache_dumper.get_extract_info()
        self._component_key = 'symbol'

    def _get_symbol_files(self, rpm_extract_dir):
        elf_files = self.cache_dumper.get_symbol_files(rpm_extract_dir)
        return elf_files

    def dump(self, repository):
        rpm_path = repository['path']
        category = repository['category'].value
        debuginfo_path = repository['debuginfo_path']
        verbose_path = os.path.basename(rpm_path)
        rpm_extract_dir = self.extract_info.get(verbose_path)
        rpm_extract_name = rpm_extract_dir.name
        if debuginfo_path:
            debuginfo_extract_name = self.extract_info.get(os.path.basename(debuginfo_path)).name
        else:
            debuginfo_extract_name = None
        if not rpm_extract_name:
            logger.exception('RPM decompression path not found')
            raise
        symbol_files = self._get_symbol_files(rpm_extract_name)
        item = {
            'rpm': verbose_path,
            'category': category,
            'debuginfo_extract_path': debuginfo_extract_name,
            'kind': self._component_key,
            'data': symbol_files
        }
        return item

    def run(self):
        dumper_list = []
        for _, repository in self.repository.items():
            dumper = self.dump(repository)
            dumper_list.append(dumper)
        return dumper_list
