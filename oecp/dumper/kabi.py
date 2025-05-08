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

import gzip

from oecp.dumper.base import AbstractDumper
from oecp.utils.kernel import get_file_by_pattern
from oecp.result.constants import CMP_TYPE_KABI


class KabiDumper(AbstractDumper):
    def __init__(self, repository, cache=None, config=None):
        super(KabiDumper, self).__init__(repository, cache, config)
        cache_require_key = 'extract'
        self.cache_dumper = self.get_cache_dumper(cache_require_key)
        self.white_list = []
        self._component_key = 'kabi'
        self.data = "data"

    @staticmethod
    def _unzip_gz(file_path):
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
        item.setdefault(self.data, [])
        if self.config.get("compare_type") == CMP_TYPE_KABI:
            self.white_list = self.cache_dumper.get_kabi_white_list()
        else:
            self.white_list = self.cache_dumper.get_drive_kabi_white_list()
        if not self.white_list:
            return [item]
        with open(symvers, "r") as f:
            for line in f.readlines():
                line = line.strip().replace("\n", "")
                if line == "":
                    continue

                hsdp = line.split()
                if len(hsdp) < 4:
                    continue

                if hsdp[1] in self.white_list:
                    item.get(self.data, []).append(
                        {'name': hsdp[1], 'symbol': "=", 'version': "%s %s %s" % (hsdp[0], hsdp[2], hsdp[3])})
        return [item]

    def run(self):
        return self.load_symvers()
