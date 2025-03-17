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

import os
import logging

from oecp.dumper.base import AbstractDumper

logger = logging.getLogger('oecp')


class HeaderDumper(AbstractDumper):
    def __init__(self, repository, cache=None, config=None):
        super(HeaderDumper, self).__init__(repository, cache, config)
        self.cache_dumper = self.get_cache_dumper(self.cache_require_key)
        self.extract_info = self.cache_dumper.get_extract_info()
        self._component_key = 'header'

    def dump(self, repository):
        rpm_path = repository['path']
        category = repository['category'].value
        verbose_path = os.path.basename(rpm_path)
        rpm_extract_dir = self.extract_info.get(verbose_path)
        rpm_extract_name = rpm_extract_dir.name
        if not rpm_extract_name:
            logger.exception('RPM decompression path not found')
        header_files = self.cache_dumper.get_header_files(rpm_extract_name)
        item = {'rpm': verbose_path, 'category': category, 'kind': self._component_key, self.data: header_files}
        return item

    def run(self):
        dumper_list = []
        for _, repository in self.repository.items():
            dumper = self.dump(repository)
            dumper_list.append(dumper)
        return dumper_list
