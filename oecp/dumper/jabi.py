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

from oecp.dumper.base import AbstractDumper

logger = logging.getLogger('oecp')


class JABIDumper(AbstractDumper):

    def __init__(self, repository, cache=None, config=None):
        super(JABIDumper, self).__init__(repository, cache, config)
        cache_require_key = 'extract'
        self.cache_dumper = self.get_cache_dumper(cache_require_key)
        self.extract_info = self.cache_dumper.get_extract_info()

    def _get_jar_files(self, rpm_extract_dir):
        jar_files = self.cache_dumper.get_jar_files(rpm_extract_dir)
        return jar_files

    def dump(self, repository):
        rpm_path = repository['path']
        verbose_path = os.path.basename(rpm_path)
        rpm_extract_dir = self.extract_info.get(verbose_path)
        rpm_extract_name = rpm_extract_dir.name
        if not rpm_extract_name:
            logger.exception('RPM decompression path not found')
            raise
        jar_files = self._get_jar_files(rpm_extract_name)
        item = {'rpm': verbose_path, 'category':  repository['category'].value, 'kind': 'jabi', 'data': jar_files}
        return item

    def run(self):
        dumper_list = []
        for _, repository in self.repository.items():
            dumper = self.dump(repository)
            dumper_list.append(dumper)
        return dumper_list
