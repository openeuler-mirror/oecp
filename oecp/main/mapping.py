# -*- encoding=utf-8 -*-
"""
# **********************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# [openeuler-jenkins] is licensed under the Mulan PSL v1.
# You can use this software according to the terms and conditions of the Mulan PSL v1.
# You may obtain a copy of Mulan PSL v1 at:
#     http://license.coscl.org.cn/MulanPSL
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v1 for more details.
# **********************************************************************************
"""
import re
import sqlite3
import os
import bz2
import gzip
from itertools import groupby

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

    @staticmethod
    def _split_version(version):
        ret = []
        if version is None:
            return ret

        for item in re.split('[_.+-]', version):
            ret += [''.join(list(g)) for k, g in groupby(item, key=lambda x: x.isdigit())]

        return ret

    @staticmethod
    def _get_flag_symbol(flag):

        return {
            "LT": "<", "LE": "<=", "EQ": "=", "GE": ">=", "GT": ">"
        }.get(flag, "")

    @staticmethod
    def _compare_signle_version(require_version, symbol, target_version):
        if require_version.isdigit():
            if target_version.isdigit():
                symbol_dict = {
                    ">=": int(target_version) >= int(require_version),
                    ">": int(target_version) > int(require_version),
                    "<=": int(target_version) <= int(require_version),
                    "<": int(target_version) < int(require_version),
                    "=": int(target_version) == int(require_version),
                }
            else:
                symbol_dict = {">=": False, ">": False, "<=": True, "<": True, "=": False}
        else:
            if target_version.isdigit():
                symbol_dict = {">=": True, ">": True, "<=": False, "<": False, "=": False}
            else:
                symbol_dict = {
                    ">=": target_version >= require_version,
                    ">": target_version > require_version,
                    "<=": target_version <= require_version,
                    "<": target_version < require_version,
                    "=": target_version == require_version,
                }
        is_eq = symbol_dict.get("=")
        if not symbol_dict.get(symbol, False):
            return is_eq, False
        return is_eq, True

    def _compare_version(self, require_version, symbol, target_version):
        is_pass = False

        if not symbol or not list(filter(lambda x: x, target_version.values())):
            return True
        for version_type in ['epoch', 'version', 'release']:
            for ver, target in zip(require_version[version_type], target_version[version_type]):
                if version_type == "epoch" and not ver:
                    continue
                is_eq, is_pass = self._compare_signle_version(ver, symbol, target)
                if not is_eq:
                    return is_pass
            require_version_len = len(require_version[version_type])
            target_version_len = len(target_version[version_type])
            if require_version_len != target_version_len and symbol != '=':
                symbol_dict = {
                    ">=": target_version_len >= require_version_len,
                    ">": target_version_len > require_version_len,
                    "<=": target_version_len <= require_version_len,
                    "<": target_version_len < require_version_len,
                }
                if not symbol_dict.get(symbol, False):
                    return False
                return True
        return is_pass

    def get_rpm_provides(self, rpm_name, database="everything"):
        provides_result = {}
        cursor = self._sqlite_conn.cursor()
        try:
            cursor.execute(f'select pkgKey from packages where name="{rpm_name}"')
            rpm_result = cursor.fetchall()
            if not rpm_result:
                logger.warning(f"No query rpm: {rpm_name} in {database} database of repodata.")
                return provides_result
            cursor.execute(f'select name,epoch,version,release from provides where pkgKey="{rpm_result[0][0]}"')
            all_provides = cursor.fetchall()
            if not all_provides:
                logger.warning(f"No query rpm: {rpm_name} provides in {database} database of repodata.")
                return provides_result
            for provide in all_provides:
                provide_info = {
                    "epoch": self._split_version(provide[1]),
                    "version": self._split_version(provide[2]),
                    "release": self._split_version(provide[3])
                }
                provides_result.setdefault(provide[0], provide_info)

        except Exception as e:
            logger.error(f"query provides from packages error,packages name={rpm_name}, databse={database}, error={e}")

        return provides_result

    def get_direct_require_rpms(self, all_provides):
        requires_packages = []
        cursor = self._sqlite_conn.cursor()
        for provide, provide_version in all_provides.items():
            cursor.execute(f'select pkgKey,flags,epoch,version,release from requires where name="{provide}"')
            require_rpms = cursor.fetchall()
            for require in require_rpms:
                symbol = self._get_flag_symbol(require[1])
                require_version = {
                    'epoch': self._split_version(require[2]),
                    'version': self._split_version(require[3]),
                    'release': self._split_version(require[4])
                }
                if symbol:
                    is_pass = self._compare_version(require_version, symbol, provide_version)
                    if not is_pass:
                        continue
                cursor.execute(f'select location_href from packages where pkgKey="{require[0]}"')
                require_rpm_name = cursor.fetchall()[0][0].split("/")[-1]
                requires_packages.append(require_rpm_name)

        return requires_packages

