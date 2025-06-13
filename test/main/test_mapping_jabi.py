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
import logging
from unittest import TestCase

from oecp.executor.base import CompareExecutor
from oecp.result.constants import CMP_TYPE_RPM_JABI
from oecp.utils.logger import init_logger


class TestProvides(TestCase):
    @classmethod
    def setUpClass(cls):
        init_logger()
        cls.logger = logging.getLogger("test")

    def test_mapping_jabi(self):
        jabi_a = [
            "abc__rpm__/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.272.b10-7.oe1.aarch64/jre/lib/jsse.jar",
            "cdb__rpm__/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.272.b10-7.oe1.aarch64/jre/lib/charsets.jar"
        ]

        jabi_b = [
            "yhg__rpm__/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.292.b10-9.oe1.aarch64/jre/lib/charsets.jar",
            "obf__rpm__/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.292.b10-9.oe1.aarch64/jre/lib/jsse.jar"
        ]

        common_jabi = [
            [
                "abc__rpm__/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.272.b10-7.oe1.aarch64/jre/lib/jsse.jar",
                "obf__rpm__/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.292.b10-9.oe1.aarch64/jre/lib/jsse.jar"
            ],
            [
                "cdb__rpm__/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.272.b10-7.oe1.aarch64/jre/lib/charsets.jar",
                "yhg__rpm__/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.292.b10-9.oe1.aarch64/jre/lib/charsets.jar"
            ]
        ]

        base = CompareExecutorTestJabi([], [])
        rpm_a = "java-1.8.0-openjdk-headless-1.8.0.272.b10-7.oe1.aarch64.rpm"
        rpm_b = "java-1.8.0-openjdk-headless-1.8.0.292.b10-9.oe1.aarch64.rpm"
        flag_n_v_d = base.extract_version_flag(rpm_a, rpm_b)
        dump_result = base.match_library_pairs(jabi_a, jabi_b, flag_n_v_d, CMP_TYPE_RPM_JABI)

        self.assertEqual(dump_result, common_jabi)


class CompareExecutorTestJabi(CompareExecutor):

    def __init__(self, dump_a, dump_b, config=None):
        super(CompareExecutorTestJabi, self).__init__(dump_a, dump_b, config)
        self.dump_a = dump_a
        self.dump_b = dump_b
        self.config = config

    def run(self):
        return []
