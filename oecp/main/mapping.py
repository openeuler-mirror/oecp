# -*- encoding=utf-8 -*-
"""
# **********************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# [openeuler-jenkins] is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# **********************************************************************************
"""
import json
import sqlite3
import os
import bz2
import gzip
from pathlib import Path

try:
    import lzma
except ImportError:
    from backports import lzma
import tempfile
import logging

from oecp.proxy.rpm_proxy import RPMProxy
from oecp.proxy.requests_proxy import do_download
from oecp.utils.misc import path_is_remote

logger = logging.getLogger("oecp")


class RepositoryPackageMapping(object):
    def __init__(self):
        pass

    def repository_of_package(self, package):
        #return RPMProxy.rpm_name(package)
        return package


class SQLiteMapping(RepositoryPackageMapping):
    def __init__(self, sqlite_path):
        """

        :param sqlite_path:
        """
        super(SQLiteMapping, self).__init__()
        self._raw_sqlite_path = sqlite_path

        self._get_connection(sqlite_path)

    def _get_connection(self, sqlite_path):
        """
        :param sqlite_path:
        :return:
        """
        # sqlite在远端
        if path_is_remote(sqlite_path):
            logger.info(f"treat {sqlite_path} as remote file")
            local_sqlite_fp = tempfile.NamedTemporaryFile("w", suffix=os.path.splitext(sqlite_path)[1])
            if do_download(sqlite_path, local_sqlite_fp.name) is None:
                raise FileNotFoundError(f"{sqlite_path} is not exist")
            sqlite_path = local_sqlite_fp.name

        # sqlite是个bz2、gz、xz文件
        if sqlite_path.endswith((".bz2", ".gz", ".xz")):
            ext = os.path.splitext(sqlite_path)[-1]
            module = {".bz2": bz2, ".gz": gzip, ".xz": lzma}.get(ext)
            logger.debug(f"sqlite file is compressed {ext} file")

            f = tempfile.NamedTemporaryFile()
            with module.open(sqlite_path, "rb") as g:
                f.write(g.read())
                f.flush()
                self._sqlite_conn = sqlite3.connect(f"{f.name}")
        else:
            logger.info(f"sqlite file path: {sqlite_path}")
            self._sqlite_conn = sqlite3.connect(f"{sqlite_path}")

    def read_rename_kernel(self):
        directory_json_path = os.path.join(Path(__file__).parents[1], 'conf', 'rename_kernel')
        with open(os.path.join(directory_json_path, 'all_rename_kernel.json'), 'r') as f:
            all_rename_kernel = json.load(f)

        return all_rename_kernel

    def repository_of_package(self, package):
        """

        :param package:
        :return:
        """
        name = RPMProxy.rpm_name(package)

        cursor = self._sqlite_conn.cursor()
        rows = cursor.execute(f"SELECT rpm_sourcerpm from packages where name=\"{name}\"")

        all_rename_kernel = self.read_rename_kernel()
        for row in rows:
            # Some iso, kernel and kernel-core repo in the rename kernel
            for rename_kernel in all_rename_kernel:
                if row[0].startswith(rename_kernel):
                    return row[0].replace(rename_kernel, 'kernel', 1)
            return row[0]

        return package

    def get_all_packages(self):
        cursor = self._sqlite_conn.cursor()
        packages = cursor.execute("SELECT * FROM packages")

        return packages
