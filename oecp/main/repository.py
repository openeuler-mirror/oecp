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
# Create: 2021-09-03
# Description: repository
# **********************************************************************************
"""
import logging
import os
import re
import sys
import traceback
from collections import UserDict
import tempfile

from oecp.proxy.rpm_proxy import RPMProxy
from oecp.result.compare_result import CompareResultComposite
from oecp.result.constants import CMP_TYPE_REPOSITORY, CMP_RESULT_TO_BE_DETERMINED, CMP_MODEL_FILE
from oecp.utils.misc import path_is_remote, basename_of_path
from oecp.proxy.requests_proxy import do_download

from oecp.utils.shell import shell_cmd

logger = logging.getLogger("oecp")


class Repository(UserDict):
    """
    多个rpm包组成一个repository
    """

    def __init__(self, work_dir, name, rpm_path, category=None):
        """

        :param work_dir: 工作目录
        :param name: repository名称
        :param rpm_path: 软件包路径
        :param category: 类别
        """
        super(Repository, self).__init__()

        self._work_dir = work_dir
        self._download_dir = None  # 如果包在远端，本地的下载路径，当不需要时删除此属性释放磁盘空间

        self._name = RPMProxy.rpm_name(name)
        self.verbose_path = os.path.basename(rpm_path)
        self.src_package = self.acquire_source_package(rpm_path)

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
        package_name = basename_of_path(verbose_path)
        name = RPMProxy.rpm_name(package_name)
        category_level = self._category.category_of_bin_package(name)
        logger.debug(f"repo {self._name} upsert a rpm, name: {name}, "
                     f"path: {path}, debuginfo_path: {debuginfo_path}, level: {category_level}")

        rpm = {
            "name": name,
            "category": category_level,
            "path": path,
            "verbose_path": verbose_path,
            "src": self.src_package,
            "raw_path": path,
            "debuginfo_path": debuginfo_path,
            "raw_debuginfo_path": debuginfo_path
        }

        self[package_name] = rpm

    def upsert_a_file(self, path, rpm_name):
        """
        增加一个文件
        @param path: 文件的完整路径
        @param rpm_name: 文件所属rpm名
        """
        file_name = os.path.basename(path)
        category_level = self._category.category_of_bin_package(rpm_name)
        file = {
            "rpm_name": rpm_name,
            "path": path,
            "src": rpm_name,
            "category": category_level,
            "model": CMP_MODEL_FILE
        }

        self[file_name] = file

    @property
    def download_dir(self):
        if self._download_dir is None:
            self._download_dir = tempfile.TemporaryDirectory(prefix="repo_", suffix=f"_{self._name}",
                                                             dir=self._work_dir)

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
            CMP_TYPE_REPOSITORY, CMP_RESULT_TO_BE_DETERMINED, self.src_package, that.src_package)

        # 比较项存在依赖关系，将config、dumper、executor缓存下来传递，缓存通过比较项名称索引
        # {"plan_name": {"config": config, "dumper": {"this": this_dumper, "that": that_dumper}, "executor": executor}}
        compare_cache = {}
        if not self.src_package.endswith('.rpm') and plan._plan_name != CMP_MODEL_FILE:
            logger.error("Please enter the correct args --plan to compare files, the value of plan name is file.")
            sys.exit(1)

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
                cache_name = compare_cache.get(name)
                cache_name.setdefault("dumper", [this_dumper, that_dumper])
                cache_name.setdefault("work_dir", self._work_dir)

                result.add_component(*executor_ins.run())
        except Exception as err:
            exstr = traceback.format_exc()
            logger.error(f"repository compare process {executor} error {err}: \n{exstr}")

        # clean cache for tempfile
        finally:
            for _, dumpers in compare_cache.items():
                for dumper in dumpers.get('dumper', []):
                    dumper.clean()

        result.set_cmp_result()

        return result

    def acquire_source_package(self, rpm_path):
        if not rpm_path.endswith('.rpm'):
            logger.debug(f"{rpm_path} is not a rpm.")
            return os.path.basename(rpm_path)
        cmd = ['rpm', '-qpi', '--nosignature', rpm_path]
        code, out, err = shell_cmd(cmd)
        if err:
            logger.warning(err)
        if out:
            r_matchs = re.finditer("Source RPM\\s+:\\s+(.*)\\n", out)
            for src_pkg in r_matchs:
                if src_pkg:
                    return src_pkg.group(1)
            logger.warning(f"Not found {rpm_path} source package.")
        return os.path.basename(rpm_path)

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
                cache_name = compare_cache.get(name)
                cache_name.setdefault("dumper", [this_dumper])
                cache_name.setdefault("work_dir", self._work_dir)

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
                cache_name = compare_cache.get(name)
                cache_name.setdefault("dumper", [this_dumper])
                cache_name.setdefault("work_dir", self._work_dir)

                res = executor_ins.run()
                result.append(res)

        # clean cache for tempfile
        finally:
            for _, dumpers in compare_cache.items():
                for dumper in dumpers.get('dumper', []):
                    dumper.clean()

        return result
