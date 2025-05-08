# -*- encoding=utf-8 -*-
"""
# **********************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# [openeuler-jenkins] is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# **********************************************************************************
"""
import sqlite3
import os
import bz2
import gzip

try:
    import lzma
except ImportError:
    from backports import lzma
import tempfile
import logging

from oecp.proxy.requests_proxy import do_download
from oecp.utils.misc import path_is_remote

logger = logging.getLogger("oecp")


class SQLiteMapping(object):
    def __init__(self, sqlite_path, log=True):
        """

        :param sqlite_path:
        """
        super(SQLiteMapping, self).__init__()
        self._raw_sqlite_path = sqlite_path

        self._get_connection(sqlite_path, log)

    def _get_connection(self, sqlite_path, log):
        """
        :param sqlite_path:
        :return:
        """
        # sqlite在远端
        if path_is_remote(sqlite_path):
            if log:
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

    def get_all_packages(self):
        cursor = self._sqlite_conn.cursor()
        packages = cursor.execute("SELECT * FROM packages")

        return packages

    def get_rpm_provides(self, rpm_name, database="everything"):
        cursor = self._sqlite_conn.cursor()
        try:
            cursor.execute(f'select pkgKey from packages where name="{rpm_name}"')
            rpm_result = cursor.fetchall()
            if not rpm_result:
                logger.warning(f"No query rpm: {rpm_name} in {database} database of repodata.")
                return []
            cursor.execute(f'select name,flags,epoch,version,release from provides where pkgKey="{rpm_result[0][0]}"')
            all_provides = cursor.fetchall()
            if not all_provides:
                logger.warning(f"No query rpm: {rpm_name} provides in {database} database of repodata.")
                return []
            provides = [provide[0] for provide in all_provides]

            return provides
        except Exception as e:
            logger.error(f"query provides from packages error,packages name={rpm_name}, databse={database}, error={e}")
            return []

    def get_direct_require_rpms(self, all_provides):
        requires_packages = []
        cursor = self._sqlite_conn.cursor()
        for provide in all_provides:
            cursor.execute(f'select pkgKey from requires where name="{provide}"')
            require_rpms = cursor.fetchall()
            if require_rpms:
                for pkgkey in require_rpms:
                    cursor.execute(f'select location_href from packages where pkgKey="{pkgkey[0]}"')
                    require_rpm_name = cursor.fetchall()[0][0].split("/")[-1]
                    requires_packages.append(require_rpm_name)

        return requires_packages

