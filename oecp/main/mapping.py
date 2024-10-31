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
import json
import sqlite3
import os
import re
import bz2
import gzip
from pathlib import Path
from itertools import groupby
from oecp.proxy.rpm_proxy import RPMProxy
from oecp.result.constants import BOOLEAN_OPERATORS

try:
    import lzma
except ImportError:
    from backports import lzma
import tempfile
import logging

from oecp.proxy.requests_proxy import do_download
from oecp.utils.misc import path_is_remote

logger = logging.getLogger("oecp")


class RepositoryPackageMapping(object):
    def __init__(self):
        pass

    def read_rename_kernel(self):
        directory_json_path = os.path.join(Path(__file__).parents[1], 'conf', 'rename_kernel')
        with open(os.path.join(directory_json_path, 'all_rename_kernel.json'), 'r') as f:
            all_rename_kernel = json.load(f)

        return all_rename_kernel

    def repository_of_package(self, package):
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

    def get_all_packages(self):
        cursor = self._sqlite_conn.cursor()
        packages = cursor.execute("SELECT * FROM packages")

        return packages

    @staticmethod
    def acquire_whole_version(cursor_record):
        epoch = cursor_record[1].strip() + ':' if cursor_record[1] else ''
        version = cursor_record[2].strip() if cursor_record[2] else ''
        release = '-' + cursor_record[3].strip() if cursor_record[3] else ''

        return epoch + version + release

    @staticmethod
    def _split_version(version):
        ret = []
        if version is None:
            return ret
        for item in re.split('[_.+-]', version):
            ret += [''.join(list(g)) for k, g in groupby(item, key=lambda x: x.isdigit())]
        return ret

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

    @staticmethod
    def filter_pkg_name(pkg):
        return pkg.strip("\(\)") not in BOOLEAN_OPERATORS

    def _compare_version(self, require_version, symbol, target_version):
        is_pass = False
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

    def _parse_version(self, spec_version):
        tmp_version = spec_version
        version = {'epoch': [], 'version': [], 'release': []}
        if ':' in tmp_version:
            epoch, tmp_version = tmp_version.split(':')[:2]
            version['epoch'] = self._split_version(epoch)
        if '-' in tmp_version:
            tmp_version, release = tmp_version.split('-')[:2]
            version['release'] = self._split_version(release)
        version['version'] = self._split_version(tmp_version)
        return version

    def is_package_name(self, name):
        pkgs = []
        matchs = re.match(r"^\(.*\)$", name)
        if matchs:
            match_result = matchs.group()
            list_pkgs = [pkg.strip("\(\)") for pkg in match_result.split()]
            pkgs = filter(self.filter_pkg_name, list_pkgs)
        else:
            regex = re.compile(r'[\w-]*')
            sub_name = regex.sub('', name)
            if not sub_name:
                pkgs.append(name)

        return pkgs

    def get_provides_rpm(self, name, symbol, version):
        package_name = []
        cursor = self._sqlite_conn.cursor()
        pkg_names = self.is_package_name(name)
        if pkg_names:
            for name in pkg_names:
                query_rpms = []
                try:
                    cursor.execute(f"select location_href from packages where location_href like '%/{name}%'")
                    rpm_result = cursor.fetchall()
                    if rpm_result:
                        for query_rpm in rpm_result:
                            query_rpms.append(query_rpm[0].split('/')[-1])
                except Exception as e:
                    logger.error(f'query location_href from packages error,packages name={name}, error={e}')
                for rpm_name in query_rpms:
                    if rpm_name and name == RPMProxy.rpm_name(rpm_name):
                        package_name.append(rpm_name)
            if package_name:
                return package_name

        cursor.execute(f"select pkgKey,epoch,version,release from provides where name='{name}'")
        result = cursor.fetchall()
        if not result and name.startswith('/'):
            cursor.execute(f"select pkgKey from files where name='{name}'")
            result = cursor.fetchall()
        if len(result) == 1:
            cursor.execute(f"select location_href from packages where pkgKey={result[0][0]}")
            rpm_result = cursor.fetchall()
            rpm_name = rpm_result[0][0].split('/')[-1]
            package_name.append(rpm_name)
        else:
            for pkginfo in result:
                cursor.execute(f"select location_href from packages where pkgKey={pkginfo[0]}")
                rpm_record = cursor.fetchall()[0]
                if version and len(pkginfo) == 4:
                    whole_version = self.acquire_whole_version(pkginfo)
                    target_version = self._parse_version(whole_version)
                    require_version = self._parse_version(version)
                    is_pass = self._compare_version(require_version, symbol, target_version)
                    if is_pass:
                        package_name.append(rpm_record[0].split('/')[-1])
                else:
                    package_name.append(rpm_record[0].split('/')[-1])

        return list(set(package_name))
