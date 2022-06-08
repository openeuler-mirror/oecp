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
# Create: 2021-09-07
# Description: test repository
# **********************************************************************************
"""
import os
import logging
from unittest import TestCase, mock

from oecp.main.category import Category, CategoryLevel
from oecp.main.directory import Directory
from oecp.main.mapping import RepositoryPackageMapping
from oecp.utils.logger import init_logger


class TestDirectory(TestCase):
    @classmethod
    def setUpClass(cls):
        init_logger()
        cls.logger = logging.getLogger("test")
        cls.test_dir_path = os.path.join(os.path.dirname(__file__), "data/rpms")

    @mock.patch.object(RepositoryPackageMapping, "repository_of_package")
    def test_construct(self, mock_repository_of_package):
        category_file = os.path.join(os.path.dirname(__file__), "data/category.json")
        category = Category(category_file)

        mock_repository_of_package.return_value = "gcc"
        directory = Directory(self.test_dir_path, work_dir="", category=category, lazy=True)
        self.assertEqual(directory, {})

        directory = Directory(self.test_dir_path, work_dir="", category=category, lazy=False)
        self.assertEqual(len(directory), 1)
        self.assertEqual("gcc" in directory, True)

    @mock.patch.object(RepositoryPackageMapping, "repository_of_package")
    def test_upsert_group(self, mock_repository_of_package):
        category_file = os.path.join(os.path.dirname(__file__), "data/category.json")
        category = Category(category_file)

        mock_repository_of_package.return_value = "gcc"
        directory = Directory(self.test_dir_path, work_dir="", category=category, lazy=True)

        directory.upsert_a_group("oe", "oe/debuginfo")

        self.assertEqual(len(directory), 1)
        self.assertEqual(len(directory["gcc"]), 2)
