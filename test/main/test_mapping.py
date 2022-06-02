# -*- encoding=utf-8 -*-
"""
# **********************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# [oecp] is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author:
# Create: 2021-09-07
# Description: test repository
# **********************************************************************************
"""
import os
import logging
from unittest import TestCase

from oecp.main.mapping import SQLiteMapping
from oecp.utils.logger import init_logger


class TestMapping(TestCase):
    @classmethod
    def setUpClass(cls):
        init_logger()
        cls.logger = logging.getLogger("test")

    #def test_construct(self):
    #    sqlite_file = os.path.join(os.path.dirname(__file__), "data/primary.sqlite")
    #    sqlite = SQLiteMapping(sqlite_file)

    #    self.assertNotEqual(getattr(sqlite, "_sqlite_conn"), None)

    def test_bz2_sqlite_file(self):
        sqlite_file = "https://repo.openeuler.org/openEuler-20.03-LTS/OS/x86_64/repodata/365dc0e1dafa37b1ea4713a519a12ad1c91adee7bf38c236398e68b1bfada497-primary.sqlite.bz2"
        sqlite = SQLiteMapping(sqlite_file)

        self.assertEqual(sqlite.repository_of_package("gcc-7.3.0-20190804"), "gcc-7.3.0-20190804.h31.oe1.oecp.rpm")
        self.assertEqual(sqlite.repository_of_package("notexist-9.3.1-20210204"), "notexist-9.3.1-20210204")
