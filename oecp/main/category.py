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
# Create: 2021-09-06
# Description: package category
# **********************************************************************************
"""
import json
import logging
import os
from enum import Enum, unique

from oecp.proxy.rpm_proxy import RPMProxy

logger = logging.getLogger("oecp")


@unique
class CategoryLevel(Enum):
    CATEGORY_LEVEL_ZERO = 0  # 核心包等级
    CATEGORY_LEVEL_ONE = 1
    CATEGORY_LEVEL_TWO = 2
    CATEGORY_LEVEL_THREE = 3
    CATEGORY_LEVEL_NOT_SPECIFIED = 4    # 未指定

    @classmethod
    def level_name_2_enum(cls, name):
        return {
            "level0": cls.CATEGORY_LEVEL_ZERO,
            "level0.5": cls.CATEGORY_LEVEL_ZERO,
            "level1": cls.CATEGORY_LEVEL_ONE,
            "level2": cls.CATEGORY_LEVEL_TWO,
            "level3": cls.CATEGORY_LEVEL_THREE}.get(name, cls.CATEGORY_LEVEL_NOT_SPECIFIED)


class Category(object):
    def __init__(self):
        """

        :param path: 分类文件，json格式
        """
        self._src_categories = {}
        self._bin_categories = {}

        self._load()

    def _load(self):
        """

        :return:
        """
        category_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "conf/category/category.json")
        try:
            with open(category_path, "r") as f:
                categories = json.load(f)

                for category in categories:
                    level = CategoryLevel.level_name_2_enum(category["level"])
                    try:
                        if category["src"]:
                            name = RPMProxy.rpm_name(category["src"])
                            self._src_categories[name] = level
                        if category["bin"]:
                            name = RPMProxy.rpm_name(category["bin"])
                            self._bin_categories[name] = level
                    except AttributeError as e:
                        logger.exception(f"\"{category['oecp']}\" or \"{category['bin']}\" is illegal rpm name")
                        raise
        except FileNotFoundError:
            logger.exception(f"{category_path} not exist")
            raise

    def category_of_src_package(self, name):
        """

        :param name:
        :return:
        """
        return self._src_categories.get(name, CategoryLevel.CATEGORY_LEVEL_NOT_SPECIFIED)

    def category_of_bin_package(self, name):
        """

        :param name:
        :return:
        """
        return self._bin_categories.get(name, CategoryLevel.CATEGORY_LEVEL_NOT_SPECIFIED)