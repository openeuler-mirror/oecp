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
# Description: compare plan
# **********************************************************************************
"""
import json
import os
import re
import logging
import importlib
from collections import UserDict
from multiprocessing import cpu_count

from oecp.result.constants import OPENEULER, CMP_TYPE_KABI, CMP_TYPE_DRIVE_KABI, X86_64, CMP_TYPE_KAPI

logger = logging.getLogger("oecp")


class Plan(UserDict):
    """

    """

    def __init__(self, args):
        """
        :param args: 主程序入口参数
        """
        super(Plan, self).__init__()

        self._type = ''
        self._base = []
        self._other = []
        self._plan = args.plan_path
        self._base_file = os.path.basename(args.compare_files[0])
        self._branch = self.cut_branch(args.branch)
        self._arch = args.arch
        self._kpath = args.src_kpath
        self._load(args.plan_path)

    @staticmethod
    def cut_branch(branch):
        os_branch = branch.lower().replace(OPENEULER, '').strip('-_.')
        return os_branch.upper()

    def _load(self, path):
        """
        加载比较计划
        :param path:
        :return:
        """
        try:
            with open(path, "r") as f:
                content = json.load(f)

                self._type = content.get('type')
                self._base = content.get('base')
                self._other = content.get('other')

                self._plan_name = content.get("name")
                self.parallel = int(content.get("parallel", cpu_count()))
                logger.debug(f"load plan {self._plan_name}")

                for item in content.get("plan"):
                    try:
                        name = item["name"]
                        config = item.get("config", dict())
                        if name in [CMP_TYPE_KABI, CMP_TYPE_DRIVE_KABI, CMP_TYPE_KAPI]:
                            self.get_cmp_branch_arch(config)
                            if name == CMP_TYPE_KAPI:
                                config["src_kernel"] = self._kpath

                        # update compare type
                        from oecp.result.constants import compare_result_name_to_attr
                        config["compare_type"] = compare_result_name_to_attr(config["compare_type"])

                        # load executor
                        module_name, class_name = name, item["executor"]
                        if "." in item["executor"]:
                            m = re.match(r"(.*)\.(.*)", item["executor"])
                            module_name, class_name = m.group(1), m.group(2)
                        logger.debug(f"load {self._plan_name}.{name} executor, {module_name}.{class_name}")
                        executor = load_module_class("oecp.executor", module_name, class_name)

                        if config.get("direct", False):
                            logger.debug(f"{self._plan_name}.{name} has direct executor")
                            self[name] = {"name": name, "direct": True, "executor": executor, "config": config}
                        else:
                            # load dumper
                            if name in [CMP_TYPE_DRIVE_KABI, CMP_TYPE_KAPI]:
                                module_name, class_name = 'kabi', item["dumper"]
                            elif name == 'lib':
                                module_name, class_name = 'abi', item["dumper"]
                            else:
                                module_name, class_name = name, item["dumper"]
                            if "." in item["dumper"]:
                                m = re.match(r"(.*)\.(.*)", item["dumper"])
                                module_name, class_name = m.group(1), m.group(2)
                            logger.debug(f"load {self._plan_name}.{name} dumper, {module_name}.{class_name}")

                            dumper = load_module_class("oecp.dumper", module_name, class_name)
                            self[item["name"]] = {"name": name, "dumper": dumper, "executor": executor,
                                                  "config": config}
                    except KeyError:
                        logger.exception(f"illegal plan, check {self._plan}")
                        raise
        except FileNotFoundError:
            logger.exception(f"{path} not exist")
            raise

    def get_type(self):
        return self._type

    def get_base(self):
        return self._base

    def get_other(self):
        return self._other

    def is_direct(self, name):
        """
        是否直接比较，abi检查
        :param name:
        :return:
        """
        return hasattr(self[name], "direct")

    def dumper_of(self, name):
        """

        :param name:
        :return: dumper类
        """
        return self[name]["dumper"]

    def executor_of(self, name):
        """

        :param name:
        :return: executor类
        """
        return self[name]["executor"]

    def config_of(self, name):
        """
        获取配置
        :param name:
        :return:
        """
        if self.get(name, []):
            return self[name].get("config", dict())

    def only_for_directory(self, name):
        """
        比较项只针对directory及其子类
        :param name:
        :return:
        """
        return self.config_of(name).get("only_directory", False)

    def check_specific_package(self, name, package_name):
        """
        计划项只针对特定的包
        :param name:
        :param package_name:
        :return:
        """
        specific_package = self.config_of(name).get("package")

        return specific_package and specific_package != package_name

    def check_specific_category(self, name, category_level):
        """
        计划项只针对特定分类的包
        :param name:
        :param category_level:
        :return:
        """
        specific_category = self.config_of(name).get("category")

        return specific_category and specific_category < category_level

    def check_sensitive_str(self, name):
        """
        
        :param name:
        :return:
        """
        return self.config_of(name).get("sensitive_str", False)

    def check_sensitive_image(self, name):
        """
        
        :param name:
        :return:
        """
        return self.config_of(name).get("sensitive_image", False)

    def get_cmp_branch_arch(self, conf):
        if self._base_file.endswith('.iso'):
            all_split_info = self._base_file.split('-')
            if all_split_info[0].lower() == OPENEULER:
                try:
                    if re.match(r"SP", all_split_info[3]):
                        version = '-'.join(all_split_info[1:4])
                        self._branch = version
                    elif "LTS" in self._base_file:
                        self._branch = '-'.join(all_split_info[1:3])
                except IndexError:
                    logger.warning(
                        f"Please check the base iso name: {self._base_file}, not get the iso branch.")
        if X86_64 in self._base_file:
            self._arch = X86_64

        conf.setdefault("branch", self._branch)
        conf.setdefault("arch", self._arch)


def load_module_class(package, module_name, class_name):
    """
    加载模块的类
    功能等价 getattr(package.module_name, class_name)

    :param module_name: 模块名
    :param package: 模块路径
    :param class_name: 类名
    :return:
    """
    try:
        module = importlib.import_module("." + module_name, package)
        return getattr(module, class_name)
    except ImportError:
        logger.exception(f"{package}.{module_name} not exist")
        raise
    except AttributeError:
        logger.exception(f"{package}.{module_name} has no attribute {class_name}")
        raise
