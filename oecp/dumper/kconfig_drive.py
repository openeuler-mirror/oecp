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
import logging
from json.decoder import JSONDecodeError
from pathlib import Path

from oecp.dumper.base import AbstractDumper
from oecp.utils.kernel import get_file_by_pattern

logger = logging.getLogger('oecp')


class KconfigDriveDumper(AbstractDumper):
    def __init__(self, repository, cache=None, config=None):
        super(KconfigDriveDumper, self).__init__(repository, cache, config)
        cache_require_key = 'extract'
        self.cache_dumper = self.get_cache_dumper(cache_require_key)
        self._component_key = 'kconfig'

    @staticmethod
    def _load_kconfig_json():
        """
        Read the json file of the key kernel driver range
        The annotations in the json file are stored as #comment options
        Returns:
            kconfig_range_data: kconfig_range_data
        """

        kconfig_json_path = Path(Path(__file__).parents[1]).joinpath("conf", "kernel_driver_range",
                                                                     "kernel_driver_range.json")
        kconfig_range_data = {}
        try:
            with open(kconfig_json_path, "r", encoding="utf-8") as file:
                kconfig_range_data = json.load(file)
        except (FileNotFoundError, JSONDecodeError):
            logger.exception("Failed to read kconfig range configuration file")
        return kconfig_range_data

    def load_kconfig_range(self):
        kconfig = get_file_by_pattern(r"^config-", self.cache_dumper)
        if not kconfig:
            kconfig = get_file_by_pattern(r"^config", self.cache_dumper)
            if not kconfig:
                return []

        kconfig_range_data = self._load_kconfig_json()
        # A collection of non-annotated phases in the configuration file
        not_annotated_config = [config_data for driver_name, config_datas in kconfig_range_data.items()
                                if driver_name != "annotation" for config_data in config_datas]
        kernel = 'kernel'
        if 'kernel-core' in kconfig:
            kernel = 'kernel-core'
        item = {
            "rpm": self.repository.get(kernel).get('verbose_path'),
            "kind": self._component_key,
            "category": self.repository.get(kernel).get('category').value,
            "data": []
        }
        with open(kconfig, "r") as f:
            for line in f.readlines():
                line = line.strip().replace("\n", "")
                if line == "":
                    continue
                if line.startswith("#"):
                    for annotation in kconfig_range_data.get("annotation"):
                        if annotation in line:
                            item.get("data").append({'name': line, 'symbol': "=", 'version': ""})
                    continue
                name, version = line.split("=", 1)
                if name in not_annotated_config:
                    item.get("data").append({'name': name, 'symbol': "=", 'version': version})
        return [item]

    def run(self):
        return self.load_kconfig_range()
