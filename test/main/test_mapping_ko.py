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
# Author:
# Create: 2023-02-22
# Description: test compare plan
# **********************************************************************************
"""
import json
import logging
import os.path
from unittest import TestCase

from oecp.executor.base import CompareExecutor
from oecp.result.constants import CMP_TYPE_KO
from oecp.utils.logger import init_logger


class TestKoinfo(TestCase):
    @classmethod
    def setUpClass(cls):
        init_logger()
        cls.logger = logging.getLogger("test")

    def test_mapping_koinfo(self):
        dir_ko_info = os.path.join(os.path.dirname(__file__), "data/ko_info/")
        with open(os.path.join(dir_ko_info, "base_info.json")) as bf:
            base_info = json.load(bf)
        with open(os.path.join(dir_ko_info, "other_info.json")) as of:
            other_info = json.load(of)
        base = CompareExecutorTestKo([], [])

        dump_result = base.format_ko_info(base_info, other_info)
        test_result = [
            [
                ['license: GPL', 'license: GPL v2', 'same'],
                ['depends: fscache,9pnet', 'depends: fscache,9pnet', 'same'],
                ['vermagic: 5.10.0-60.18.0.50.oe2203.aarch64 SMP mod_unload modversions aarch64',
                 'vermagic: 5.10.0-136.12.0.86.oe2203sp1.aarch64 SMP mod_unload modversions aarch64', 'same'],
                ['ko symbol:  kobject_put 0xd7b82d67', 'ko symbol:  kobject_put 0xd7b82d67', 'same'],
                ['ko symbol:  __mark_inode_dirty 0xa207317e', 'ko symbol:  __mark_inode_dirty 0xa207317e', 'same']
            ],
            [
                ['srcversion: 5BF0E117803A440640410D1', 'srcversion: 40D379DD1C5D5D87115ADFF', 'diff'],
                [
                    'alias: pci:v000015B3d00001021sv*sd*bc*sc*i*\npci:v000015B3d0000A2D2sv*sd*bc*sc*i*\npci:v000015B3d'
                    '0000A2D3sv*sd*bc*sc*i*\npci:v000015B3d0000A2D6sv*sd*bc*sc*i*',
                    'alias: pci:v000015B3d0000A2D2sv*sd*bc*sc*i*\npci:v000015B3d0000A2D3sv*sd*bc*sc*i*\npci:v000015B3d'
                    '0000A2D6sv*sd*bc*sc*i*',
                    'diff']
            ],
            [],
            [
                ['', 'ko symbol:  filemap_fault 0xa5ac95f1', 'more']
            ]
        ]

        self.assertEqual(dump_result, test_result)


class CompareExecutorTestKo(CompareExecutor):

    def __init__(self, dump_a, dump_b, config=None):
        super(CompareExecutorTestKo, self).__init__(dump_a, dump_b, config)
        self.dump_a = dump_a
        self.dump_b = dump_b
        self.config = config
        self.data = 'data'

    def mapping_ko_files(self, base_dump):
        mapping_ko = self.split_files_mapping(base_dump[self.data], CMP_TYPE_KO)

        return mapping_ko

    @staticmethod
    def run():
        return []
