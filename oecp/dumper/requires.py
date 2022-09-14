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

from oecp.utils.shell import shell_cmd
from oecp.dumper.base import ComponentsDumper

logger = logging.getLogger('oecp')


class RequiresDumper(ComponentsDumper):

    def __init__(self, repository, cache=None, config=None):
        super(RequiresDumper, self).__init__(repository, cache, config)
        self._requires_cmd = ['rpm', '-pq', '--requires', '--nosignature']
        self._recommends_cmd = ['rpm', '-pq', '--recommends', '--nosignature']
        self._component_key = 'requires'

    def get_rpm_requires(self, dependence_type,  cmd):
        requires = []
        added_requires = []
        code, out, err = shell_cmd(cmd)
        if not code:
            if err:
                logger.warning(err)
            if out:
                for line in out.split("\n"):
                    if not line:
                        continue
                    r = re.match("(\S+)\s([><=]=?)\s(\S+)", line)
                    try:
                        if r:
                            name, symbol, version = r.groups()
                        else:
                            name, symbol, version = line, '', ''
                        require_str = '-'.join([name, symbol, version])
                        if require_str not in added_requires:
                            added_requires.append(require_str)
                            requires.append({'name': name, 'symbol': symbol, 'version': version,
                                             'dependence': dependence_type})
                    except Exception:
                        logger.warning("{}".format(line))
        return requires

    def dump(self, repository):
        result = {}
        rpm_path = repository['path']
        if not self._requires_cmd:
            raise ValueError('%s should be command list' % self._requires_cmd)
        if not self._recommends_cmd:
            raise ValueError('%s should be command list' % self._recommends_cmd)

        requires_data = self.get_rpm_requires('strict', self._requires_cmd + [rpm_path])
        recommends_data = self.get_rpm_requires('weak', self._recommends_cmd + [rpm_path])
        requires_data.extend(recommends_data)
        result.setdefault(self._data, []).extend(requires_data)
        if result:
            result.setdefault('rpm', os.path.basename(rpm_path))
            result.setdefault('kind', self._component_key)
            result.setdefault('category', repository['category'].value)
        return result

    def run(self):
        dumper_list = []
        for _, repository in self.repository.items():
            dumper = self.dump(repository)
            dumper_list.append(dumper)
        return dumper_list
