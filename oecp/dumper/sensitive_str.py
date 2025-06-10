# -*- encoding=utf-8 -*-
"""
# **********************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# [oecp] is licensed under the Mulan PSL v1.
# You can use this software according to the terms and conditions of the Mulan PSL v1.
# You may obtain a copy of Mulan PSL v1 at:
#     http://license.coscl.org.cn/MulanPSL
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v1 for more details.
# **********************************************************************************
"""

import os
import logging
import tempfile
import shutil
from oecp.dumper.base import ComponentsDumper
from oecp.utils.shell import shell_cmd

logger = logging.getLogger('oecp')


class SensitiveStrDumper(ComponentsDumper):

    def __init__(self, repository, cache=None, config=None):
        super(SensitiveStrDumper, self).__init__(repository, cache, config)
        self._cmd = ['grep', '-rinI', config.get('target')]
        self._component_key = 'sensitive_str'
        self._rpm_path = None
        self._tmp = []

    def clean(self):
        for tmp_path in self._tmp:
            if os.path.exists(tmp_path):
                shutil.rmtree(tmp_path)

    def dump(self, repository):
        rpm_path = repository['path']
        
        dump_list = []
        if os.path.exists(rpm_path):
            tmp_path = tempfile.mkdtemp()
            self._tmp.append(tmp_path)
            cmd = f"cd {tmp_path} && rpm2cpio {rpm_path} | cpio -div"
            os.system(cmd)
            cmd = self._cmd + [tmp_path]
            
            code, out, err = shell_cmd(cmd)
            if not code:
                if err:
                    logger.warning(err)
                if out:
                    for line in out.split("\n"):
                        if not line:
                            continue
                        line = line.strip(tmp_path)
                        dump_list.append(line)
        item = {'rpm': os.path.basename(rpm_path), 'kind': self._component_key, 'data': dump_list}
        item.setdefault('category', repository['category'].value)
        return item

    def run(self):
        dumper_list = []
        for _, repository in self.repository.items():
            dumper = self.dump(repository)
            dumper_list.append(dumper)
        return dumper_list

