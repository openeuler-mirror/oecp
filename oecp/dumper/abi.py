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


class ABIDumper(AbstractDumper):

    def __init__(self, repository, cache=None, config=None):
        super(ABIDumper, self).__init__(repository, cache, config)
        # 依赖rpm解压对象，暂时先写死，todo: 后面通过config字典中加入{'require': 'extract'}获取此dumper对应的依赖
        cache_require_key = 'extract'
        self.cache_dumper = self.get_cache_dumper(cache_require_key)
        self.extract_info = self.cache_dumper.get_extract_info()

    def dump(self, repository):
        rpm_path = repository['path']
        debuginfo_path = repository['debuginfo_path']
        rpm_extract_dir = self.extract_info.get(os.path.basename(rpm_path))
        rpm_extract_name = rpm_extract_dir.name
        rpm_extract_linkfile = rpm_extract_name + "_linkfile"
        if debuginfo_path:
            debuginfo_extract_name = self.extract_info.get(os.path.basename(debuginfo_path)).name
        else:
            debuginfo_extract_name = None
        if not rpm_extract_name:
            logger.exception('RPM decompression path not found')
        library_files = self.cache_dumper.get_library_files(rpm_extract_name)
        link_files = self.cache_dumper.get_library_files(rpm_extract_linkfile)
        item = {'rpm': os.path.basename(rpm_path),
                'debuginfo_extract_path': debuginfo_extract_name,
                'category': repository['category'].value,
                'kind': 'abi',
                'data': library_files,
                'link_file': link_files}
        return item

    def run(self):
        dumper_list = []
        for _, repository in self.repository.items():
            dumper = self.dump(repository)
            dumper_list.append(dumper)
        return dumper_list
