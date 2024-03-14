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


class ServiceDumper(AbstractDumper):
    def __init__(self, repository, cache=None, config=None):
        super(ServiceDumper, self).__init__(repository, cache, config)
        self._component_key = 'service'

    def dump(self, repository):
        category = repository['category'].value
        if self.cmp_model:
            verbose_path = repository.get('rpm_name')
            service_files = [repository.get('path')]
        else:
            cache_dumper = self.get_cache_dumper(self.cache_require_key)
            extract_info = cache_dumper.get_extract_info()
            verbose_path = os.path.basename(repository['path'])
            rpm_extract_dir = extract_info.get(verbose_path)
            rpm_extract_name = rpm_extract_dir.name
            if not rpm_extract_name:
                logger.exception('RPM decompression path not found')
            service_files = cache_dumper.get_service_files(rpm_extract_name)

        item = {
            'rpm': verbose_path,
            'category': category,
            'kind': self._component_key,
            'data': service_files,
            'model': self.cmp_model
        }
        return item

    def run(self):
        dumper_list = []
        for _, repository in self.repository.items():
            dumper = self.dump(repository)
            dumper_list.append(dumper)
        return dumper_list
