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
import re
from oecp.utils.shell import shell_cmd

logger = logging.getLogger('oecp')


class PackageListDumper:

    def __init__(self, directory, config=None):
        self.config = config if config else {}
        self.directory = directory
        self.data = 'data'

    def dump(self):
        item = {}
        for repo, repo_item in self.directory.items():
            for rpm_name in repo_item:
                rpm = repo_item[rpm_name]['verbose_path']
                category = repo_item[rpm_name]['category'].value
                source_package = repo_item.verbose_path
                if not source_package.endswith('.src.rpm'):
                    fp = repo_item[rpm_name]['path']
                    cmd = ['rpm', '-qpi', '--nosignature', fp]
                    code, out, err = shell_cmd(cmd)
                    if err:
                        logger.warning(err)
                    if out:
                        for line in out.split("\n"):
                            if not line:
                                continue
                            r = re.match("Source RPM\s+:\s+(.*)", line)
                            if r:
                                source_package = r.group(1)
                                break

                attr = {'category': category, 'source_package': source_package}
                item.setdefault(rpm, attr)
        result = {'path': self.directory.verbose_path, self.data: item}
        return result

    def run(self):
        result = self.dump()
        return result
