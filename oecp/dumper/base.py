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
import json
import os
import re
import logging

from abc import ABC, abstractmethod
from oecp.proxy.rpm_proxy import RPMProxy
from oecp.utils.shell import shell_cmd
from oecp.result.constants import CMP_MODEL_FILE, X86_64, AARCH64

logger = logging.getLogger('oecp')


class AbstractDumper(ABC):

    def __init__(self, repository, cache=None, config=None):
        """
        @param repository: Repository类的实例
        """
        self.repository = repository
        self.cache = cache if cache else {}
        self.config = config if config else {}
        self.cache_require_key = 'extract'
        self.data = 'data'
        self.kabi_white_list = []
        self.drive_kabi_white_list = []
        self.cmp_model = next(iter(repository.values())).get('model') == CMP_MODEL_FILE

    @staticmethod
    def get_branch_dir(dir_kabi_whitelist, white_branch):
        with open(os.path.join(dir_kabi_whitelist, "white_list_branch.json"), "r") as jf:
            branch_mapping = json.load(jf)

        for branch_dir, all_branchs in branch_mapping.items():
            if white_branch in all_branchs:
                return branch_dir
        logger.debug(f"branch {white_branch} not get correct path.")
        return ""

    @staticmethod
    def open_the_whitelist(kabi_whitelist, white_list):
        try:
            with open(kabi_whitelist, "r") as f:
                for line in f.readlines()[1:]:
                    white_list.append(line.strip().replace("\n", ""))
        except FileNotFoundError as err:
            logger.debug(f"Please check kabi whitelist: {kabi_whitelist} not exist, error: {err}")

    def get_cache_dumper(self, cache_require_key):
        tar_dumper = None
        cache_dumpers = self.cache.get(cache_require_key, {}).get('dumper')
        if not cache_dumpers:
            logger.exception(f'No cache {cache_require_key} dumper')
        else:
            for cache_dumper in cache_dumpers:
                if cache_dumper.repository is not self.repository:
                    continue
                else:
                    tar_dumper = cache_dumper
                    break
        return tar_dumper

    def load_white_list(self, rpm_name):
        dir_kabi_whitelist = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                          "conf/kabi_whitelist")
        _, _, _, _, parse_arch = RPMProxy.rpm_n_v_r_d_a(rpm_name)
        white_branch = self.config.get('branch')
        param_arch = self.config.get('arch')
        arch = param_arch if param_arch else parse_arch
        logger.debug(f"kabi whitelist get branch: {white_branch}, arch: {arch}")
        if arch not in [X86_64, AARCH64]:
            logger.error(f"kabi whitelist arch error: {arch}")

        drive_kabi_whitelist = os.path.join(dir_kabi_whitelist, arch + "_drive_kabi")
        self.open_the_whitelist(drive_kabi_whitelist, self.drive_kabi_white_list)

        branch_dir = self.get_branch_dir(dir_kabi_whitelist, white_branch)
        kabi_whitelist = os.path.join(dir_kabi_whitelist, branch_dir, arch)
        self.open_the_whitelist(kabi_whitelist, self.kabi_white_list)

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
                    r = re.match("(\\S+)\\s([><=]=?)\\s(\\S+)", line)
                    try:
                        if r:
                            name, symbol, version = r.groups()
                            item.setdefault(self.data, []).append(
                                {'name': name, 'symbol': symbol, 'version': version})
                        else:
                            name = line
                            item.setdefault(self.data, []).append(
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
