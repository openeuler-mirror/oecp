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
import re
import logging

from oecp.dumper.base import AbstractDumper
from oecp.utils.kernel import get_file_by_pattern


class KconfigDumper(AbstractDumper):
    def __init__(self, repository, cache=None, config=None):
        super(KconfigDumper, self).__init__(repository, cache, config)
        cache_require_key = 'extract'
        self.cache_dumper = self.get_cache_dumper(cache_require_key)
        self._component_key = 'kconfig'
        self.data = "data"

    def load_kconfig(self):
        if not self.cache_dumper:
            return []
        kconfig, kernel = get_file_by_pattern(r"^config-", self.cache_dumper)
        # CentOS-8.2.2004-aarch64-dvd1.iso 中config文件的文件名为：config
        if not kconfig:
            kconfig, kernel = get_file_by_pattern(r"^config", self.cache_dumper)
            if not kconfig:
                return []

        item = {}
        item.setdefault('rpm', self.repository.get(kernel).get('verbose_path'))
        item.setdefault('kind', self._component_key)
        item.setdefault('category', self.repository.get(kernel).get('category').value)
        with open(kconfig, "r") as f:
            for line in f.readlines():
                line = line.strip().replace("\n", "")
                if line == "":
                    continue
                if line.startswith("#"):
                    continue

                name, version = line.split("=", 1)
                item.setdefault(self.data, []).append({'name': name, 'symbol': "=" , 'version': version})
        return [item]

    def run(self):
        return self.load_kconfig()


