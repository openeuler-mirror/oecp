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
# Description: test rpm filelist compare
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
            "/lib/modules/6.1.8-3.0.0.8.oe1.x86_64/vdso/.build-id/78/86b97f3ee72fb93a07229abe016c48b9d8ddaa.debug_[link]_../../vdso64.so",
            "/lib/modules/6.1.8-3.0.0.8.oe1.x86_64/vdso/.build-id/6a/e8fc067b96a9c115a223a72596999c1afdc970.debug_[link]_../../vdso32.so"
        ]
        file_b = [
            "/lib/modules/6.1.8-3.0.0.9.oe1.x86_64/vdso/.build-id/74/1534e4fb0604d5043d2a9f37191106f409f8aa.debug_[link]_../../vdso32.so",
            "/lib/modules/6.1.8-3.0.0.9.oe1.x86_64/vdso/.build-id/1a/28ad71204fd5d8cc64bd84a158571d7ca21b48.debug_[link]_../../vdso64.so"
        ]
        common_filelist = [
            ["/lib/modules/6.1.8-3.0.0.8.oe1.x86_64/vdso/.build-id/6a/e8fc067b96a9c115a223a72596999c1afdc970.debug_[link]_../../vdso32.so",
             "/lib/modules/6.1.8-3.0.0.9.oe1.x86_64/vdso/.build-id/1a/28ad71204fd5d8cc64bd84a158571d7ca21b48.debug_[link]_../../vdso64.so",
             'changed'],
            ["/lib/modules/6.1.8-3.0.0.8.oe1.x86_64/vdso/.build-id/78/86b97f3ee72fb93a07229abe016c48b9d8ddaa.debug_[link]_../../vdso64.so",
             "/lib/modules/6.1.8-3.0.0.9.oe1.x86_64/vdso/.build-id/74/1534e4fb0604d5043d2a9f37191106f409f8aa.debug_[link]_../../vdso32.so",
             'changed']
        ]
        base = CompareExecutorTestFilelist([], [])
        rpm_a = "kernel-6.1.8-3.0.0.8.oe1.x86_64.rpm"
        rpm_b = "kernel-6.1.8-3.0.0.9.oe1.x86_64.rpm"
        flag_n_v_d = base.extract_version_flag(rpm_a, rpm_b)
        dump_result = base.format_dump(file_a, file_b, flag_n_v_d)
        self.assertEqual(dump_result[1], common_filelist)

    def test_clear_file_ext(self):
        base = CompareExecutorTestFilelist([], [])
        file_name = "nouveau.ko.xz"
        clear_file_name = base.clear_file_change_ext(file_name)

        self.assertEqual(clear_file_name, "nouveau.ko")

    def test_mapping_files(self):
        base = CompareExecutorTestFilelist([], [])
        flag_nvd = "6.1.8-3.0.0.8.oe1"
        dist = "oe1"
        files = [
            "/lib/modules/6.1.8-3.0.0.8.oe1.x86_64/vdso/.build-id/78/86b97f3ee72fb93a07229abe016c48b9d8ddaa.debug_[link]_../../vdso64.so"
        ]
        result = base.mapping_files(files, flag_nvd, dist)
        print(result)


class CompareExecutorTestFilelist(CompareExecutor):

    def __init__(self, dump_a, dump_b, config=None):
        super(CompareExecutorTestFilelist, self).__init__(dump_a, dump_b, config)
        self.dump_a = dump_a
        self.dump_b = dump_b
        self.config = config

    def compare(self):
        result = {}
        if hasattr(self.dump_a, 'run') and hasattr(self.dump_a, 'run'):
            self.dump_a.run()
            self.dump_b.run()

        return result

    def run(self):
        result = self.compare()
        return result
