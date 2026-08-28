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
from oecp.result.constants import CMP_TYPE_DRIVE_KABI, CMP_TYPE_KABI
from oecp.utils.kernel import get_file_by_pattern


class KabiDumper(AbstractDumper):
    def __init__(self, repository, cache=None, config=None):
        super().__init__(repository, cache, config)
        self.cmp_type = config.get("compare_type")
        self._white_list = self.kabi_white_list

    @staticmethod
    def _unzip_gz(file_path):
        f_name = file_path[0:file_path.rindex('.')]
        with gzip.GzipFile(file_path) as g_file, open(f_name, "wb+") as f:
            f.write(g_file.read())

    def load_symvers(self, repository):
        rpm_name = repository.get('verbose_path')
        if self.cmp_model:
            symvers = repository.get('path')
            rpm_name = repository.get('rpm_name')
        else:
            cache_dumper = self.get_cache_dumper(self.cache_require_key)
            symvers = get_file_by_pattern(r"^symvers", cache_dumper, rpm_name)
        if not symvers:
            return []

        if symvers.endswith('.gz'):
            self._unzip_gz(symvers)
            symvers = symvers[0:symvers.rindex('.')]

        item = {}
        item.setdefault('rpm', rpm_name)
        item.setdefault('kind', CMP_TYPE_KABI)
        item.setdefault('category', repository['category'].value)
        item.setdefault(self.data, [])
        self.load_white_list(rpm_name)
        if self.config.get("compare_type") == CMP_TYPE_DRIVE_KABI:
            self._white_list = self.drive_kabi_white_list
        with open(symvers, "r") as f:
            for line in f:
                line = line.strip().replace("\n", "")
                if line == "":
                    continue

                hsdp = line.split()
                if len(hsdp) < 4:
                    continue

                if self._white_list and hsdp[1] not in self._white_list:
                    continue
                item.get(self.data, []).append(
                    {'name': hsdp[1], 'symbol': "=", 'version': f"{hsdp[0]} {hsdp[2]} {hsdp[3]}"})
        return [item]

    def run(self):
        result = []
        for repository in self.repository.values():
            result.extend(self.load_symvers(repository))
        return result
