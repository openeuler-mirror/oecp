# -*- encoding=utf-8 -*-
"""
# **********************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# [oecp] is licensed under the Mulan PSL v1.
# You can use this software according to the terms and conditions of the Mulan PSL v1.
# You may obtain a copy of Mulan PSL v1 at:
#     http://license.coscl.org.cn/MulanPSL
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v1 for more details.
# Author:
# Create: 2021-09-03
# Description: repository
# **********************************************************************************
"""
import os
import logging
from collections import UserDict
import tempfile
import weakref

from oecp.utils.misc import path_is_remote, basename_of_path
from oecp.proxy.requests_proxy import do_download
from oecp.proxy.rpm_proxy import RPMProxy
from oecp.result.compare_result import *

logger = logging.getLogger("oecp")


class Repository(UserDict):
    """
    多个rpm包组成一个repository
    """
    def __init__(self, work_dir, name, category=None):
        """

        :param work_dir: 工作目录
        :param name: repository名称
        :param category: 类别
        """
        super(Repository, self).__init__()

        self._work_dir = work_dir
        self._download_dir = None  # 如果包在远端，本地的下载路径，当不需要时删除此属性释放磁盘空间

        self._name = RPMProxy.rpm_name(name)
        self.verbose_path = name

        self._category = category
        self._category_level = category.category_of_src_package(self._name)

    @property
    def work_dir(self):
        return self._work_dir

    def upsert_a_rpm(self, path, verbose_path, debuginfo_path=None):
        """
        增加一个rpm包
        :param path: 包完整路径
        :param verbose_path: 包展示路径
        :param debuginfo_path: debuginfo包完整路径
        :return:
        """
        name = RPMProxy.rpm_name(basename_of_path(verbose_path))
        category_level = self._category.category_of_bin_package(name)
        logger.debug(f"repo {self._name} upsert a rpm, name: {name}, "
                     f"path: {path}, debuginfo_path: {debuginfo_path}, level: {category_level}")

        rpm = {
            "name": name,
            "category": category_level,
            "path": path,
            "verbose_path": verbose_path,
            "raw_path": path,
            "debuginfo_path": debuginfo_path,
            "raw_debuginfo_path": debuginfo_path
        }

        self[name] = rpm

    @property
    def download_dir(self):
        if self._download_dir is None:
            self._download_dir = tempfile.TemporaryDirectory(prefix="repo_", suffix=f"_{self._name}", dir=self._work_dir)

        return self._download_dir.name

    @download_dir.setter
    def download_dir(self, path):
        self._download_dir = path

    @download_dir.deleter
    def download_dir(self):
        """
        释放下载的包占用的磁盘空间
        :return:
        """
        self._download_dir = None

    def __getitem__(self, item):
        """
        某些rpm的路径是远端时，此处会执行下载动作
        :param item:
        :return:
        """
        rpm = super(Repository, self).__getitem__(item)

        # download rpm rpm lazy
        path = rpm.get("path")
        if path_is_remote(path):
            local_path = os.path.join(self.download_dir, basename_of_path(path))
            do_download(path, local_path)
            rpm["path"] = local_path

        # download debuginfo rpm lazy
        debuginfo_path = rpm.get("debuginfo_path")
        if path_is_remote(debuginfo_path):
            local_path = os.path.join(self.download_dir, basename_of_path(debuginfo_path))
            do_download(debuginfo_path, local_path)
            rpm["debuginfo_path"] = local_path

        return rpm

    def clean(self):
        """

        :return:
        """
        self.download_dir = None

    def compare(self, that, plan):
        """
        执行比较
        :param that: 比较另一方
        :param plan: 比较计划
        :return:
        """
        result = CompareResultComposite(
            CMP_TYPE_REPOSITORY, CMP_RESULT_TO_BE_DETERMINED, self.verbose_path, that.verbose_path)

        # 比较项存在依赖关系，将config、dumper、executor缓存下来传递，缓存通过比较项名称索引
        # {"plan_name": {"config": config, "dumper": {"this": this_dumper, "that": that_dumper}, "executor": executor}}
        compare_cache = {}

        try:
            for name in plan:
                if plan.only_for_directory(name):
                    logger.debug(f"ignore plan.{name} for repository")
                    continue

                if plan.check_specific_package(name, self._name):
                    logger.debug(f"plan.{name} not support {self._name}")
                    continue

                if plan.check_specific_category(name, self._category_level):
                    logger.debug(f"plan.{name} not support {self._category_level}")
                    continue

                logger.info(f"Analysis repo {self._name} [{name}]")

                # get dumper, executor, config
                dumper = plan.dumper_of(name)
                executor = plan.executor_of(name)
                config = plan.config_of(name)

                compare_cache.setdefault(name, {})
                this_dumper, that_dumper = dumper(self, compare_cache, config), dumper(that, compare_cache, config)
                executor_ins = executor(this_dumper, that_dumper, config)

                # set cache
                compare_cache[name]["dumper"] = [this_dumper, that_dumper]
                compare_cache[name]["work_dir"] = self._work_dir
                # compare_cache[name]["executor"] = weakref.proxy(executor_ins)

                result.add_component(*executor_ins.run())

        # clean cache for tempfile
        finally:
            for _, dumpers in compare_cache.items():
                for dumper in dumpers.get('dumper', []):
                    dumper.clean()

        result.set_cmp_result()

        return result

    def find_sensitive_str(self, plan):
        """
        执行查找
        :param plan: 查找计划
        :return:
        """
        result = []

        # 比较项存在依赖关系，将config、dumper、executor缓存下来传递，缓存通过比较项名称索引
        # {"plan_name": {"config": config, "dumper": {"this": this_dumper, "that": that_dumper}, "executor": executor}}
        compare_cache = {}

        try:
            for name in plan:

                if not plan.check_sensitive_str(name):
                    logger.debug(f"plan.{name} not support {self._name}")              
                    continue

                logger.info(f"Analysis repo {self._name} [{name}]")

                # get dumper, executor, config
                dumper = plan.dumper_of(name)
                executor = plan.executor_of(name)
                config = plan.config_of(name)

                compare_cache.setdefault(name, {})
                this_dumper = dumper(self, compare_cache, config)
                executor_ins = executor(this_dumper, config)

                # set cache
                compare_cache[name]["dumper"] = [this_dumper]
                compare_cache[name]["work_dir"] = self._work_dir
                # compare_cache[name]["executor"] = weakref.proxy(executor_ins)

                res = executor_ins.run()
                result.append(res)

        # clean cache for tempfile
        finally:
            for _, dumpers in compare_cache.items():
                for dumper in dumpers.get('dumper', []):
                    dumper.clean()

        return result

    def find_sensitive_image(self, plan):
        """
        执行查找
        :param plan: 查找计划
        :return:
        """
        result = []

        # 比较项存在依赖关系，将config、dumper、executor缓存下来传递，缓存通过比较项名称索引
        # {"plan_name": {"config": config, "dumper": {"this": this_dumper, "that": that_dumper}, "executor": executor}}
        compare_cache = {}

        try:
            for name in plan:
                if not plan.check_sensitive_image(name):
                    logger.debug(f"plan.{name} not support {self._name}")              
                    continue

                logger.info(f"compare repo {self._name} [{name}]")

                # get dumper, executor, config
                dumper = plan.dumper_of(name)
                executor = plan.executor_of(name)
                config = plan.config_of(name)

                compare_cache.setdefault(name, {})
                this_dumper = dumper(self, compare_cache, config)
                executor_ins = executor(this_dumper, config)

                # set cache
                compare_cache[name]["dumper"] = [this_dumper]
                compare_cache[name]["work_dir"] = self._work_dir
                # compare_cache[name]["executor"] = weakref.proxy(executor_ins)
                res = executor_ins.run()
                result.append(res)

        # clean cache for tempfile
        finally:
            for _, dumpers in compare_cache.items():
                for dumper in dumpers.get('dumper', []):
                    dumper.clean()

        return result
