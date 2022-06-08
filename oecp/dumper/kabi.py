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

import re
import os
import gzip
import logging

from oecp.dumper.base import AbstractDumper
from oecp.utils.kernel import get_file_by_pattern

class KabiDumper(AbstractDumper):
    def __init__(self, repository, cache=None, config=None):
        super(KabiDumper, self).__init__(repository, cache, config)
        cache_require_key = 'extract'
        self.cache_dumper = self.get_cache_dumper(cache_require_key)
        self.white_list = []
        self.load_white_list()
        self._component_key = 'kabi'
        self.data = "data"

    def _unzip_gz(self, file_path):
        g_file = gzip.GzipFile(file_path)
        f_name = file_path[0:file_path.rindex('.')]
        open(f_name, "wb+").write(g_file.read())
        g_file.close()

    def load_symvers(self):
        symvers = get_file_by_pattern(r"^symvers", self.cache_dumper)
        if not symvers:
            return []

        if symvers.endswith('.gz'):
            self._unzip_gz(symvers)
            symvers = symvers[0:symvers.rindex('.')]

        item = {}
        kernel = 'kernel'
        if 'kernel-core' in symvers:
            kernel = 'kernel-core'
        item.setdefault('rpm', self.repository.get(kernel).get('verbose_path'))
        item.setdefault('kind', self._component_key)
        item.setdefault('category', self.repository.get(kernel).get('category').value)
        with open(symvers, "r") as f:
            for line in f.readlines():
                line = line.strip().replace("\n", "")
                if line == "":
                    continue

                hsdp = line.split()
                if len(hsdp) < 4:
                    continue

                if hsdp[1] in self.white_list:
                    item.setdefault(self.data, []).append({'name': hsdp[1], 'symbol': "=" , 'version': "%s %s %s"%(hsdp[0], hsdp[2], hsdp[3])})
        return [item]

    def load_white_list(self):
        white_file = self.config.get('white_list')
        if not white_file.startswith("/"):
            white_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "conf", white_file)
        with open(white_file, "r") as f:
            for line in f.readlines()[1:]:
                self.white_list.append(line.strip().replace("\n", ""))

    def run(self):
        return self.load_symvers()

