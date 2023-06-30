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
import json
import re

from oecp.dumper.base import AbstractDumper
from oecp.result.constants import FILTER_PATTERN, NO_FILES
from oecp.utils.shell import shell_cmd

logger = logging.getLogger('oecp')


class FileListDumper(AbstractDumper):

    def __init__(self, repository, cache=None, config=None):
        super(FileListDumper, self).__init__(repository, cache, config)
        cache_require_key = "extract"
        self.cache_dumper = self.get_cache_dumper(cache_require_key)
        self.extract_info = self.cache_dumper.get_extract_info()
        self._cmd = ['rpm', '-pql', '--nosignature']
        self.link_flag = "_[link]_"
        self.white_rpm = "/conf/rpm_white/rpm_name_list.json"

    @staticmethod
    def filter_attention_files(line):
        for filter_pattern in FILTER_PATTERN.values():
            if re.match(filter_pattern, line) or "metadata_list-compact" in line:
                return True

        return False

    def dump(self, repository):
        rpm_path = repository['path']
        white_file_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + self.white_rpm
        rpm_extract_dir = self.extract_info.get(os.path.basename(rpm_path))
        with open(white_file_path, 'r') as rpm_name_list:
            white_list = json.load(rpm_name_list)
        dump_list = []
        code, out, err = shell_cmd(self._cmd + [rpm_path])
        if not code:
            if err:
                logger.warning(err)
            if out:
                for line in out.split("\n"):
                    if not line or NO_FILES in line:
                        continue
                    if self.filter_attention_files(line):
                        continue
                    if repository['name'] in white_list['rpm_name_list']:
                        dump_list.append(os.path.basename(line))
                    else:
                        full_path = os.path.join(rpm_extract_dir.name, line.lstrip('/'))
                        if os.path.islink(full_path):
                            link_tar = [line, self.link_flag, str(os.readlink(full_path)).lstrip('./')]
                            dump_list.append(''.join(link_tar))
                        else:
                            dump_list.append(line)
        item = {'rpm': os.path.basename(rpm_path), 'kind': 'filelist', 'data': dump_list}
        item.setdefault('category', repository['category'].value)
        return item

    def run(self):
        dumper_list = []
        for _, repository in self.repository.items():
            dumper = self.dump(repository)
            dumper_list.append(dumper)
        return dumper_list
