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
# Description: test rpm compatibility category
# **********************************************************************************
"""
import os
import logging
from unittest import TestCase

from oecp.main.category import Category, CategoryLevel
from oecp.utils.logger import init_logger


class TestCategory(TestCase):
    @classmethod
    def setUpClass(cls):
        init_logger()
        cls.logger = logging.getLogger("test")

    def test_construct(self):
        category_file = os.path.join(os.path.dirname(__file__), "data/category.json")
        category = Category(category_file)
        self.assertIsNotNone(getattr(category, "_src_categories"))
        self.assertIsNotNone(getattr(category, "_bin_categories"))

    def test_category_file_not_found(self):
        category_file = os.path.join(os.path.dirname(__file__), "data/data_not_found")

        with self.assertRaises(FileNotFoundError):
            Category(category_file)

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
        self.assertEqual(category.category_of_src_package(""), CategoryLevel.CATEGORY_LEVEL_NOT_SPECIFIED)
