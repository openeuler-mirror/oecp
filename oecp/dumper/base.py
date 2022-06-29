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

from abc import ABC, abstractmethod
from oecp.utils.shell import shell_cmd


logger = logging.getLogger('oecp')


class AbstractDumper(ABC):

    def __init__(self, repository, cache=None, config=None):
        """

        @param repository: Repository类的实例
        """
        self.repository = repository
        self.cache = cache if cache else {}
        self.config = config if config else {}

    def get_cache_dumper(self, cache_require_key):
        cache_dumpers = self.cache.get(cache_require_key, {}).get('dumper')
        if not cache_dumpers:
            logger.exception(f'No cache {cache_require_key} dumper')
            raise
        for cache_dumper in cache_dumpers:
            if cache_dumper.repository is self.repository:
                return cache_dumper
        logger.exception(f'Get cache {cache_require_key} dumper fail')
        raise

    def clean(self):
        pass

    @abstractmethod
    def run(self):
        pass


class ComponentsDumper(AbstractDumper):

    def __init__(self, repository, cache=None, config=None):
        super(ComponentsDumper, self).__init__(repository, cache, config)
        self._cmd = None
        self._component_key = None
        self._data = 'data'

    def dump(self, repository):
        rpm_path = repository['path']
        item = {}
        cmd = self._cmd
        if not cmd:
            raise ValueError('%s should be command list' % cmd)
        cmd = cmd + [rpm_path]
        code, out, err = shell_cmd(cmd)
        if not code:
            if err:
                logger.warning(err)
            if out:
                item.setdefault('rpm', os.path.basename(rpm_path))
                item.setdefault('kind', self._component_key)
                item.setdefault('category', repository['category'].value)
                for line in out.split("\n"):
                    if not line:
                        continue
                    r = re.match("(\S+)\s([><=]=?)\s(\S+)", line)
                    try:
                        if r:
                            name, symbol, version = r.groups()
                            item.setdefault(self._data, []).append(
                                {'name': name, 'symbol': symbol, 'version': version})
                        else:
                            name = line
                            item.setdefault(self._data, []).append(
                                {'name': name, 'symbol': '', 'version': ''})
                    except Exception:
                        logger.warning("{}".format(line))
        return item

    def run(self):
        dumper_list = []
        for _, repository in self.repository.items():
            dumper = self.dump(repository)
            dumper_list.append(dumper)
        return dumper_list
