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

from oecp.main.category import Category, CategoryLevel
from oecp.main.repository import Repository
from oecp.utils.logger import init_logger


class TestRepository(TestCase):
    @classmethod
    def setUpClass(cls):
        init_logger()
        cls.logger = logging.getLogger("test")

    def test_construct(self):
        category_file = os.path.join(os.path.dirname(__file__), "data/category.json")
        category = Category(category_file)

        repo = Repository("data", "gcc", category)

        self.assertEqual(getattr(repo, "_category_level"), CategoryLevel.CATEGORY_LEVEL_ONE)

    def test_upsert_rpm(self):
        category_file = os.path.join(os.path.dirname(__file__), "data/category.json")
        category = Category(category_file)

        repo = Repository("data", "gcc", category)
        repo.upsert_a_rpm("data/rpms/oe/gcc-7.3.0-20190804.h31.oe1.aarch64.rpm",
                          "gcc-7.3.0-20190804.h31.oe1.aarch64.rpm",
                          "data/rpms/oe/debuginfo/gcc-debuginfo-7.3.0-20190804.h31.oe1.aarch64")
        repo.upsert_a_rpm("data/rpms/oe/gcc-plugin-devel-7.3.0-20190804.h31.oe1.aarch64.rpm",
                          "gcc-plugin-devel-7.3.0-20190804.h31.oe1.aarch64.rpm",
                          "data/rpms/oe/debuginfo/gcc-plugin-devel-debuginfo-7.3.0-20190804.h31.oe1.aarch64.rpm")
        repo.upsert_a_rpm("data/rpms/oe/libasan-7.3.0-20190804.h31.oe1.aarch64.rpm",
                          "libasan-7.3.0-20190804.h31.oe1.aarch64.rpm",
                          "data/rpms/oe/debuginfo/libasan-debuginfo-7.3.0-20190804.h31.oe1.aarch64.rpm")
        repo.upsert_a_rpm("data/rpms/oe/libatomic-7.3.0-20190804.h31.oe1.aarch64.rpm",
                          "libatomic-7.3.0-20190804.h31.oe1.aarch64.rpm",
                          "data/rpms/oe/debuginfo/libatomic-debuginfo-7.3.0-20190804.h31.oe1.aarch64.rpm")

        self.assertEqual(repo["gcc"]["name"], "gcc")
        self.assertEqual(repo["gcc-plugin-devel"]["category"], CategoryLevel.CATEGORY_LEVEL_ONE)
        self.assertEqual(repo["libasan"]["path"], "data/rpms/oe/libasan-7.3.0-20190804.h31.oe1.aarch64.rpm")
        self.assertEqual(repo["libatomic"]["verbose_path"], "libatomic-7.3.0-20190804.h31.oe1.aarch64.rpm")
        self.assertEqual(repo["gcc"]["raw_path"], "data/rpms/oe/gcc-7.3.0-20190804.h31.oe1.aarch64.rpm")
        self.assertEqual(repo["gcc-plugin-devel"]["debuginfo_path"], "data/rpms/oe/debuginfo/gcc-plugin-devel-debuginfo-7.3.0-20190804.h31.oe1.aarch64.rpm")
        self.assertEqual(repo["libatomic"]["raw_debuginfo_path"], "data/rpms/oe/debuginfo/libatomic-debuginfo-7.3.0-20190804.h31.oe1.aarch64.rpm")

        with self.assertRaises(KeyError):
            _ = repo["libgcc"]

        self.assertEqual(tuple([item for item in repo]), ('gcc', 'gcc-plugin-devel', 'libasan', 'libatomic'))

    def test_category_item(self):
        category_file = os.path.join(os.path.dirname(__file__), "data/category.json")
        category = Category(category_file)

        self.assertEqual(category.category_of_bin_package("gcc"), CategoryLevel.CATEGORY_LEVEL_ONE)
        self.assertEqual(category.category_of_bin_package("coreutils"), CategoryLevel.CATEGORY_LEVEL_TWO)
        self.assertEqual(category.category_of_bin_package("man-db"), CategoryLevel.CATEGORY_LEVEL_THREE)
        self.assertEqual(category.category_of_bin_package("cairo"), CategoryLevel.CATEGORY_LEVEL_NOT_SPECIFIED)
        self.assertEqual(category.category_of_src_package("gcc"), CategoryLevel.CATEGORY_LEVEL_ONE)
        self.assertEqual(category.category_of_src_package("coreutils"), CategoryLevel.CATEGORY_LEVEL_TWO)
        self.assertEqual(category.category_of_src_package("man-db"), CategoryLevel.CATEGORY_LEVEL_THREE)
        self.assertEqual(category.category_of_bin_package("cairo"), CategoryLevel.CATEGORY_LEVEL_NOT_SPECIFIED)
