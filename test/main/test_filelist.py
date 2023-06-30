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
# Create: 2023-02-25
# Description: test compare plan
# **********************************************************************************
"""
import logging
from unittest import TestCase

from oecp.executor.base import CompareExecutor
from oecp.utils.logger import init_logger


class TestFilelists(TestCase):
    @classmethod
    def setUpClass(cls):
        init_logger()
        cls.logger = logging.getLogger("test")

    def test_mapping_filelist(self):
        file_a = [
            "/lib/modules/4.19.90-2112.8.0.0131.oe1.aarch64/kernel/arch/arm64/crypto/aes-ce-blk.ko",
            "/lib/modules/4.19.90-2112.8.0.0131.oe1.aarch64/kernel/arch/arm64/crypto/aes-ce-ccm.ko"
        ]
        file_b = [
            "/lib/modules/5.10.0-136.12.0.86.oe2203sp1.aarch64/kernel/arch/arm64/crypto/aes-ce-blk.ko.xz",
            "/lib/modules/5.10.0-136.12.0.86.oe2203sp1.aarch64/kernel/arch/arm64/crypto/aes-ce-ccm.ko.xz"
        ]
        common_filelist = [
                ["/lib/modules/4.19.90-2112.8.0.0131.oe1.aarch64/kernel/arch/arm64/crypto/aes-ce-blk.ko",
                 "/lib/modules/5.10.0-136.12.0.86.oe2203sp1.aarch64/kernel/arch/arm64/crypto/aes-ce-blk.ko.xz",
                 'File format changed'],
                ["/lib/modules/4.19.90-2112.8.0.0131.oe1.aarch64/kernel/arch/arm64/crypto/aes-ce-ccm.ko",
                 "/lib/modules/5.10.0-136.12.0.86.oe2203sp1.aarch64/kernel/arch/arm64/crypto/aes-ce-ccm.ko.xz",
                 'File format changed']
            ]
        base = CompareExecutorTestFilelist([], [])
        rpm_a = "kernel-4.19.90-2112.8.0.0131.oe1.aarch64.rpm"
        rpm_b = "kernel-5.10.0-136.12.0.86.oe2203sp1.aarch64.rpm"
        flag_n_v_d = base.extract_version_flag(rpm_a, rpm_b)
        dump_result = base.format_dump(file_a, file_b, flag_n_v_d)
        self.assertEqual(dump_result[1], common_filelist)

    def test_clear_file_ext(self):
        base = CompareExecutorTestFilelist([], [])
        file_name = "nouveau.ko.xz"
        clear_file_name = base.clear_file_change_ext(file_name)

        self.assertEqual(clear_file_name, "nouveau.ko")


class CompareExecutorTestFilelist(CompareExecutor):

    def __init__(self, dump_a, dump_b, config=None):
        super(CompareExecutorTestFilelist, self).__init__(dump_a, dump_b, config)
        self.dump_a = dump_a
        self.dump_b = dump_b
        self.config = config

    def run(self):
        return []
