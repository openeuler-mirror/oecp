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
# Create: 2023-11-02
# Description: test rpm compatibility category
# **********************************************************************************
"""

from unittest import TestCase

from oecp.executor.base import CompareExecutor


class TestCategory(TestCase):
    def test_map_provides(self):
        base_components = [
            {'name': 'kernel', 'symbol': '=', 'version': '5.10.0-136.52.0.131.oe2203sp1'},
            {'name': 'python3.7dist(ansible)', 'symbol': '=', 'version': '2.5.5'},
            {'name': 'python2dist(b43-debug-tools)', 'symbol': '=', 'version': '0'},
            {'name': 'kernel=5.10.0-136.52.0.131.oe2203sp1.aarch64', 'symbol': '', 'version': ''},
            {'name': 'libdbus-1.so.3(LIBDBUS_PRIVATE_1.12.16)(64bit)', 'symbol': '', 'version': ''},
            {'name': 'git', 'symbol': '<=', 'version': '2.27.0'}
        ]

        other_components = [
            {'name': 'kernel', 'symbol': '=', 'version': '5.10.0-136.12.0.86.h1283.eulerosv2r12'},
            {'name': 'python3.9dist(ansible)', 'symbol': '=', 'version': '2.9.27'},
            {'name': 'python3dist(b43-debug-tools)', 'symbol': '=', 'version': '0'},
            {'name': 'kernel=5.10.0-136.12.0.86.h1283.eulerosv2r12.aarch64', 'symbol': '', 'version': ''},
            {'name': 'libdbus-1.so.3(LIBDBUS_PRIVATE_1.12.20)(64bit)', 'symbol': '', 'version': ''},
            {'name': 'git', 'symbol': '<=', 'version': '2.33.0'}
        ]

        base = CompareExecutorTestFilelist([], [])
        rpm_a = "kernel-5.10.0-136.52.0.131.oe2203sp1.aarch64.rpm"
        rpm_b = "kernel-5.10.0-136.12.0.86.h1283.eulerosv2r12.aarch64.rpm"
        rpm_version_release_dist = base.extract_version_flag(rpm_a, rpm_b)
        component_results = base.format_dump_provides(base_components, other_components, rpm_version_release_dist)

        result = [[['kernel = 5.10.0', 'kernel = 5.10.0', 'same'],
                   ['python3.7dist(ansible) = 2.5.5', 'python3.9dist(ansible) = 2.9.27', 'same'],
                   ['python2dist(b43-debug-tools) = 0', 'python3dist(b43-debug-tools) = 0', 'same'],
                   ['kernel=5.10.0-136.52.0.131.oe2203sp1.aarch64  ',
                    'kernel=5.10.0-136.12.0.86.h1283.eulerosv2r12.aarch64  ', 'same'],
                   ['libdbus-1.so.3(LIBDBUS_PRIVATE_1.12.16)(64bit)  ',
                    'libdbus-1.so.3(LIBDBUS_PRIVATE_1.12.20)(64bit)  ', 'same'],
                   ['git <= 2.27.0', 'git <= 2.33.0', 'same']], [], []]

        self.assertEqual(component_results, result)


class CompareExecutorTestFilelist(CompareExecutor):

    def __init__(self, base_dump, other_dump, config=None):
        super(CompareExecutorTestFilelist, self).__init__(base_dump, other_dump, config)
        self.base_dump = base_dump
        self.other_dump = other_dump
        self.config = config

    def compare(self):
        result = {}
        if hasattr(self.base_dump, 'run') and hasattr(self.base_dump, 'run'):
            self.base_dump.run()
            self.other_dump.run()

        return result

    def run(self):
        result = self.compare()
        return result
