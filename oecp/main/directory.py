# -*- encoding=utf-8 -*-
"""
# **********************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# [oecp] is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author:
# Create: 2021-09-03
# Description: directory
# **********************************************************************************
"""
import logging
from collections import UserDict, defaultdict
import os
import re
import tempfile
from multiprocessing import Pool, cpu_count

from .repository import Repository
from .mapping import RepositoryPackageMapping, SQLiteMapping

from oecp.result.compare_result import *
from oecp.proxy.rpm_proxy import RPMProxy
from oecp.proxy.requests_proxy import do_download
from oecp.utils.shell import shell_cmd

from bs4 import BeautifulSoup as bs
from defusedxml.ElementTree import parse

logger = logging.getLogger("oecp")


class Directory(UserDict):
    def __init__(self, path, work_dir, category, lazy=True):
        """

        :param path: 目录路径
        :param work_dir: 工作目录
        :param category: 包分类对象
        """
        super(Directory, self).__init__()

        self._path = path
        self.verbose_path = path

        self._work_dir = work_dir

        self._cmp_type = CMP_TYPE_DIRECTORY

        self._category = category

        self._lazy = lazy

        # 加载当前目录，rpm和debuginfo包都在当前目录
        if not self._lazy:
            self.upsert_a_group(".", ".")

    def _all_debuginfo_rpm(self, debuginfo_path):
        """

        :param debuginfo_path: debuginfo包所在的子路径
        :return:
        """
        if not debuginfo_path:
            logger.info("debuginfo path not specify")
            return {}

        debuginfo_full_path = os.path.realpath(os.path.join(self._path, debuginfo_path))
        if not os.path.exists(debuginfo_full_path):
            logger.info(f"{debuginfo_full_path} not exists")
            return {}

        all_debuginfo_rpm = {}
        for file in os.listdir(debuginfo_full_path):
            file_path = os.path.join(debuginfo_full_path, file)
            if os.path.isfile(file_path) and RPMProxy.is_debuginfo_rpm(file):
                all_debuginfo_rpm[file] = file_path

        return all_debuginfo_rpm

    def _all_focus_on_rpm(self, path):
        """

        :param path: rpm所在的子路径
        :return:
        """
        if not path:
            logger.info("rpm package path not specify")
            return {}

        rpm_full_path = os.path.realpath(os.path.join(self._path, path))
        if not os.path.exists(rpm_full_path):
            logger.info(f"{rpm_full_path} not exists")
            return {}

        all_rpm = {}
        for file in os.listdir(rpm_full_path):
            file_path = os.path.join(rpm_full_path, file)
            if os.path.isfile(file_path) and RPMProxy.is_rpm_file(file_path) and RPMProxy.is_rpm_focus_on(file):
                all_rpm[file] = file_path

        return all_rpm

    def upsert_a_group(self, path, debuginfo_path=None, sqlite_path=None):
        """
        增加一个子目录
        :param path: 组的rpm包所在的子路径
        :param debuginfo_path: 组的debuginfo包所在的子路径
        :param sqlite_path: 组的sqlite文件路径
        :return:
        """
        logger.info(f"{self.verbose_path} upsert a group, path: {path}, debuginfo: {debuginfo_path}, sqlite: {sqlite_path}")

        mapping = SQLiteMapping(os.path.join(self._path, sqlite_path)) if sqlite_path else RepositoryPackageMapping()
        focus_on_rpm = self._all_focus_on_rpm(path)
        debuginfo_rpm = self._all_debuginfo_rpm(debuginfo_path)
        logger.info(f"{self.verbose_path} total {len(focus_on_rpm)} rpm packages, {len(debuginfo_rpm)} debuginfo packages")
        for rpm, rpm_path in focus_on_rpm.items():
            repository_full_name = mapping.repository_of_package(rpm)
            repository_name = RPMProxy.rpm_name(repository_full_name)
            correspond_debuginfo_rpm = RPMProxy.correspond_debuginfo_name(rpm)
            if repository_name in self:
                self[repository_name].upsert_a_rpm(rpm_path, rpm, debuginfo_rpm.get(correspond_debuginfo_rpm))
            else:
                self[repository_name] = Repository(self._work_dir, repository_full_name, self._category)
                self[repository_name].upsert_a_rpm(rpm_path, rpm, debuginfo_rpm.get(correspond_debuginfo_rpm))

    def _parallel_compare(self, that, plan, pool_size=0):
        """

        :param that:
        :param plan:
        :param pool_size: 进程池大小
        :return:
        """
        pool = Pool(pool_size or cpu_count())
        jobs = []

        # 比较每一个repository
        try:
            for repository in self:
                if repository not in that:
                    logger.warning(f"{repository} not in {that.verbose_path}")
                    continue
                jobs.append(pool.apply_async(self.compare_job, (self[repository], that[repository], plan)))
        except KeyboardInterrupt:
            pool.terminate()
        pool.close()
        return [job.get() for job in jobs]

    @staticmethod
    def compare_job(side_a, side_b, plan):
        try:
            return side_a.compare(side_b, plan)
        finally:
            side_a.clean()
            side_b.clean()

    def _in_order_compare(self, that, plan):
        """

        :param that:
        :param plan:
        :return:
        """
        result = []
        # 比较每一个repository
        for repository in self:
            if repository not in that:
                logger.warning(f"{repository} not in {that.verbose_path}")
                continue

            side_a = self[repository]
            side_b = that[repository]
            try:
                result.append(self.compare_job(side_a, side_b, plan))
            finally:
                side_a.clean()
                side_b.clean()

        return result

    def compare(self, that, plan):
        """

        :param that: 比较对手
        :param plan: 比较计划
        :return:
        """
        result = CompareResultComposite(self._cmp_type, CMP_RESULT_TO_BE_DETERMINED, self.verbose_path, that.verbose_path)

        # 目录层比较
        for name in plan:
            if not plan.only_for_directory(name):
                continue
            logger.info(f"compare directory [{name}]")
            dumper = plan.dumper_of(name)
            executor = plan.executor_of(name)
            config = plan.config_of(name)
    
            this_dumper, that_dumper = dumper(self), dumper(that)
            executor_ins = executor(this_dumper, that_dumper, config)
    
            result.add_component(executor_ins.run())

        # 比较每一个repository
        if plan.parallel:
            [result.add_component(rc) for rc in self._parallel_compare(that, plan, plan.parallel)]
        else:
            [result.add_component(rc) for rc in self._in_order_compare(that, plan)]

        result.set_cmp_result()

        return result


class DistISO(Directory):
    """
    iso文件
    """
    # path = "/a.iso,/a-debug.iso" with_debug=True
    # path = "/a.iso"
    def __init__(self, path, work_dir, category, with_debug=False):
        self._debuginfo_iso = ''
        self._rpm_iso = ''

        if with_debug:
            path = self._format_path(path)
            self._rpm_iso = path.split(',')[0]
            self._debuginfo_iso = path.split(',')[1]
        else:
            self._rpm_iso = path
        super(DistISO, self).__init__(self._rpm_iso, work_dir, category)

        self._cmp_type = CMP_TYPE_ISO
        self.verbose_path = os.path.basename(self._rpm_iso)

        self._mounts = {}
        self._mount_paths = {}
        self._iso_packages_sqlite={}

    def _format_path(self, path):
        if ',' not in path:
            path = path + ','
        return path

    def _mount_iso(self, iso_path):
        if not iso_path or self._mounts.get(iso_path):
            return

        _mount_dir = tempfile.TemporaryDirectory(prefix="iso_", suffix=f"_{self.verbose_path}", dir=self._work_dir)
        mount_dir_name = _mount_dir.name

        mount_cmd = "mount -o loop {} {}".format(iso_path, mount_dir_name)
        ret, out, err = shell_cmd(mount_cmd.split())

        if ret:
            if ret == 32:
                # permission denied
                logger.info("mount iso permission denied, try sudo")
                mount_cmd = "sudo mount -o loop {} {}".format(iso_path, mount_dir_name)
                ret, out, err = shell_cmd(mount_cmd.split())
                if ret == 0:
                    self._mounts[iso_path] = True
                    self._mount_paths[iso_path] = _mount_dir
                    return

            logger.error(f"mount file error: {ret}, {err}")

        self._mounts[iso_path] = True
        self._mount_paths[iso_path] = _mount_dir

    def _umount_iso(self, iso_path):
        if not self._mounts.get(iso_path):
            return

        _mount_path = self._mount_paths.get(iso_path).name
        unmount_cmd = "umount {}".format(_mount_path)
        ret, out, err = shell_cmd(unmount_cmd.split())

        if ret:
            if ret == 32:
                # permission denied
                logger.info("umount iso permission denied, try sudo")
                unmount_cmd = "sudo umount {}".format(_mount_path)
                ret, out, err = shell_cmd(unmount_cmd.split())
                if ret == 0:
                    self._mounts[iso_path] = False
                    return
            logger.error(f"umount file error: {ret}, {err}")

        self._mounts[iso_path] = False

    def find_primary_sqlite_path(self):
        """
        找到repodata目录下下primary.sqlite文件
        :return:
        """
        # 同源ISO的repodata放在BaseOS目录下
        for repodata_dir in ["repodata", "BaseOS/repodata"]:
            try:
                repodata_path = os.path.join(self._mount_dir.name, repodata_dir)

                for file in os.listdir(repodata_path):
                    if re.match(r"^[0-9a-z]+-primary\.sqlite.(bz2|gz|xz)$", file):
                        return os.path.join(repodata_path, file)
            except FileNotFoundError:
                continue

    def _set_iso_packages_sqlite_paths(self, iso):
        if not iso:
            return

        _mount_path = self._mount_paths.get(iso).name
        packages2sqlite = {}
        for root, dirs, files in os.walk(_mount_path):
            for f in files:
                if '-primary.sqlite.' not in f:
                    continue
                ff = os.path.join(root, f)
                sf = ff.split('/repodata/')[0]
                if '/Packages/repodata/' in ff:
                    packages2sqlite[sf] = ff
                else:
                    packages2sqlite[os.path.join(sf, 'Packages')] = ff
        self._iso_packages_sqlite[iso] = packages2sqlite

    def compare(self, that, plan):
        try:
            self._mount_iso(self._rpm_iso)
            self._mount_iso(self._debuginfo_iso)
            self._set_iso_packages_sqlite_paths(self._rpm_iso)
            self._set_iso_packages_sqlite_paths(self._debuginfo_iso)
            logger.debug("self _iso_packages_sqlite", self._iso_packages_sqlite)
            self_all_debuginfo_rpm = self._all_debuginfo_rpm(self._debuginfo_iso)
            _packages_sqlite = self._iso_packages_sqlite.get(self._rpm_iso)
            for k, v in _packages_sqlite.items():
                self.upsert_a_group(k, v, self_all_debuginfo_rpm)

            that._mount_iso(that._rpm_iso)
            that._mount_iso(that._debuginfo_iso)
            that._set_iso_packages_sqlite_paths(that._rpm_iso)
            that._set_iso_packages_sqlite_paths(that._debuginfo_iso)
            logger.debug("that _iso_packages_sqlite", that._iso_packages_sqlite)
            that_all_debuginfo_rpm = that._all_debuginfo_rpm(that._debuginfo_iso)
            _packages_sqlite = that._iso_packages_sqlite.get(that._rpm_iso)
            for k, v in _packages_sqlite.items():
                that.upsert_a_group(k, v, that_all_debuginfo_rpm)

            return super(DistISO, self).compare(that, plan)
        finally:
            self._umount_iso(self._rpm_iso)
            self._umount_iso(self._debuginfo_iso)
            that._umount_iso(that._rpm_iso)
            that._umount_iso(that._debuginfo_iso)

    def upsert_a_group(self, packages_path, sqlite=None, debuginfo_rpm={}):
        mapping = SQLiteMapping(sqlite) if sqlite else RepositoryPackageMapping()
        focus_on_rpm = self._all_focus_on_rpm(packages_path)
        logger.info(f"{self.verbose_path} total {len(focus_on_rpm)} rpm packages, {len(debuginfo_rpm)} debuginfo packages")
        for rpm, rpm_path in focus_on_rpm.items():
            repository_full_name = mapping.repository_of_package(rpm)
            repository_name = RPMProxy.rpm_name(repository_full_name)
            correspond_debuginfo_rpm = RPMProxy.correspond_debuginfo_name(rpm)
            if repository_name in self:
                self[repository_name].upsert_a_rpm(rpm_path, rpm, debuginfo_rpm.get(correspond_debuginfo_rpm))
            else:
                self[repository_name] = Repository(self._work_dir, repository_full_name, self._category)
                self[repository_name].upsert_a_rpm(rpm_path, rpm, debuginfo_rpm.get(correspond_debuginfo_rpm))

    def _all_focus_on_rpm(self, packages_path):
        if not os.path.exists(packages_path):
            logger.info(f"{packages_path} not exists")
            return {}

        all_rpm = {}
        for f in os.listdir(packages_path):
            fp = os.path.join(packages_path, f)
            if os.path.isfile(fp) and RPMProxy.is_rpm_file(fp) and RPMProxy.is_rpm_focus_on(f):
                all_rpm[f] = fp

        return all_rpm

    def _all_debuginfo_rpm(self, debuginfo_iso):
        if not debuginfo_iso:
            return {}

        logger.debug(f'debuginfo iso is {debuginfo_iso}, iso packages sqlite is {self._iso_packages_sqlite}')
        debuginfo_packages = self._iso_packages_sqlite.get(debuginfo_iso)
        all_debuginfo_rpm = {}
        for k, v in debuginfo_packages.items():
            all_debuginfo_rpm.update(self._get_debuginfo_rpm(k))

        return all_debuginfo_rpm

    def _get_debuginfo_rpm(self, debuginfo_path):
        logger.info(f'debuginfo path is {debuginfo_path}')
        if not os.path.exists(debuginfo_path):
            logger.info(f"{debuginfo_path} not exists")
            return {}

        debuginfo_rpm = {}
        for f in os.listdir(debuginfo_path):
            fp = os.path.join(debuginfo_path, f)
            if os.path.isfile(fp) and RPMProxy.is_debuginfo_rpm(f):
                debuginfo_rpm[f] = fp

        return debuginfo_rpm

class OEDistRepo(Directory):
    def __init__(self, paths, work_dir, category, arch=None):
        super(OEDistRepo, self).__init__('', work_dir, category)

        self._work_dir = work_dir
        self._cmp_type = CMP_TYPE_DIST_REPOSITORY
        self._sqlite_paths = {}

        # paths
        # - "https://repo.openeuler.org/openEuler-20.03-LTS-SP1/EPOL/aarch64/repodata, https://repo.openeuler.org/openEuler-20.03-LTS-SP1/debuginfo/aarch64/repodata"
        # - "https://repo.openeuler.org/openEuler-20.03-LTS-SP1/everything/aarch64/repodata, https://repo.openeuler.org/openEuler-20.03-LTS-SP1/debuginfo/aarch64/repodata"
        self._format_paths(paths)

        for _path in paths:
            _rpm_path, _debuginfo_path = _path.split(',')
            self._set_primary_sqlite_path(_rpm_path)
            self._set_primary_sqlite_path(_debuginfo_path)
            self.upsert_a_group(_rpm_path, _debuginfo_path, self._get_primary_sqlite_path(_rpm_path))

    def _format_paths(self, paths):
        """
        # input paths
        # - "https://repo.openeuler.org/openEuler-20.03-LTS-SP1/EPOL/aarch64/repodata/, https://repo.openeuler.org/openEuler-20.03-LTS-SP1/debuginfo/aarch64/repodata/"
        # - "https://repo.openeuler.org/openEuler-20.03-LTS-SP1/everything/aarch64/repodata

        # output paths
        # - "https://repo.openeuler.org/openEuler-20.03-LTS-SP1/EPOL/aarch64/repodata,https://repo.openeuler.org/openEuler-20.03-LTS-SP1/debuginfo/aarch64/repodata"
        # - "https://repo.openeuler.org/openEuler-20.03-LTS-SP1/everything/aarch64/repodata,
        """
        for i, _path in enumerate(paths):
            if ',' not in _path:
                 _path = _path + ','
            _path = _path.replace('/,', ',')

            if _path.endswith('/'):
                _path = _path[:-1]

            paths[i] = _path.replace(' ', '')

    def upsert_a_group(self, path, debuginfo_path=None, sqlite_path=None):
        """
        增加一个子目录
        :param path: 组的rpm包所在的子路径
        :param debuginfo_path: 组的debuginfo包所在的子路径
        :param sqlite_path: 组的sqlite文件路径
        :return:
        """
        logger.info(f"upsert a group, path: {path}, debuginfo: {debuginfo_path}, sqlite: {sqlite_path}")

        mapping = SQLiteMapping(sqlite_path) if sqlite_path else RepositoryPackageMapping()
        focus_on_rpm = self._all_focus_on_rpm(path)
        debuginfo_rpm = self._all_debuginfo_rpm(debuginfo_path)
        logger.info(f"{len(focus_on_rpm)} rpm packages, {len(debuginfo_rpm)} debuginfo packages")
        for rpm, rpm_path in focus_on_rpm.items():
            repository_full_name = mapping.repository_of_package(rpm)
            repository_name = RPMProxy.rpm_name(repository_full_name)
            correspond_debuginfo_rpm = RPMProxy.correspond_debuginfo_name(rpm)
            if repository_name in self:
                self[repository_name].upsert_a_rpm(rpm_path, rpm, debuginfo_rpm.get(correspond_debuginfo_rpm))
            else:
                self[repository_name] = Repository(self._work_dir, repository_full_name, self._category)
                self[repository_name].upsert_a_rpm(rpm_path, rpm, debuginfo_rpm.get(correspond_debuginfo_rpm))


    def _set_primary_sqlite_path(self, repodata_path):
        if not repodata_path:
            logger.info("repodata path is not specify")
            return

        repomd_xml_url = os.path.join(repodata_path, 'repomd.xml')
        rs = self.parse_repomd_xml(repomd_xml_url)

        for f in rs:
            if re.search(r"[0-9a-z]+-primary\.sqlite.*$", f):
                # rs[f] = repodata/58ec880d69c9da6625ae7fa9bc07ea521e6e939b0b917fe9e227d3d1bda05e60-primary.sqlite.bz2
                self._sqlite_paths[repodata_path] = os.path.join('/'.join(repodata_path.split('/')[:-1]), rs[f])

    def _get_primary_sqlite_path(self, repodata_path):
        if not repodata_path:
            logger.info("repodata path is not specify")
            return None

        return self._sqlite_paths.get(repodata_path, None)


    def parse_repomd_xml(self, repomd_xml_url):
        if not repomd_xml_url:
            logger.info("repomd xml url is not specify")
            return {}

        tmp_dir = tempfile.TemporaryDirectory(prefix="oe_dist_repo_", suffix="_Packages", dir=self._work_dir)
        repomd_xml_local = os.path.join(tmp_dir.name, 'repomd.xml')
        if do_download(repomd_xml_url, repomd_xml_local) is None:
            return {}

        rs = {}
        et = parse(repomd_xml_local)
        root_node = et.getroot()

        for data_node in root_node:
            for location in data_node.iter():
                if location.tag.endswith('location'):
                    rs[location.get('href')] = location.get('href')
        return rs

    def find_primary_sqlite_path(self, sqlite_path):
        """
        找到repodata目录下下primary.sqlite文件
        :return:
        """
        if not sqlite_path:
            logger.info("debuginfo path not specify")
            return {}

        sqlite_full_path = os.path.join(self._path, sqlite_path)

        logger.debug(f"search primary.sqlite file at {sqlite_full_path}")
        rs = self._prepare_package_info(sqlite_full_path, sqlite=True)

        for file in rs:
            if re.match(r"^[0-9a-z]+-primary\.sqlite.*$", file):
                return os.path.join(sqlite_path, rs[file])

    def _prepare_package_info_old(self, package_html_url, debuginfo=False, sqlite=False):
        """
        计算所有需要比对的包
        1. 忽略doc、help等包
        2. 相同的包，取时间最近的
        :return:
        """
        tmp_dir = tempfile.TemporaryDirectory(prefix="oe_dist_repo_", suffix="_Packages", dir=self._work_dir)
        package_html_local = os.path.join(tmp_dir.name, "packages.html")

        if do_download(package_html_url, package_html_local) is None:
            return {}

        # 解析packages列表
        rs = {}
        with open(package_html_local, "r") as f:
            soup = bs(f.read(), 'html.parser')
            # <td><a href=anaconda-33.19-19.oe1.x86_64.rpm></td><td>64.3 KiB</td><td>2021-Apr-01 16:58</td>
            for a in soup.find_all("a"):
                package = a['href']
                if package.split('.')[-1] not in ['rpm', 'gz', 'bz2']:
                    continue

                if sqlite:
                    #rs[package] = os.path.join(package_html_url, package)
                    rs[package] = package
                    continue
                if debuginfo:
                    if RPMProxy.is_debuginfo_rpm(package):
                        rs[package] = os.path.join(package_html_url, package)
                else:
                    if RPMProxy.is_rpm_file(package) and not RPMProxy.is_debuginfo_rpm(package):
                        rs[package] = os.path.join(package_html_url, package)

        return rs

    def _prepare_package_info(self, package_path, debuginfo=False):
        if not package_path:
            return {}

        #package_full_path = os.path.join(self._path, package_path)
        package_full_path = package_path
        _sqlite_path = self._sqlite_paths.get(package_path, None)
        logger.debug(f"package_path={package_path},package_full_path={package_full_path},sqlite_path={_sqlite_path},sqlite_paths={self._sqlite_paths}")
        if not _sqlite_path:
            return {}

        tmp_dir = tempfile.TemporaryDirectory(prefix="oe_dist_repo_", suffix="_Packages", dir=self._work_dir)
        sqlite = SQLiteMapping(_sqlite_path)
        packages = sqlite.get_all_packages()
        rs = {}

        for package in packages:
            location_href = package[23]
            package_name = location_href.split('/')[-1]
            if debuginfo:
                if RPMProxy.is_debuginfo_rpm(package_name):
                    rs[package_name] = os.path.join('/'.join(package_path.split('/')[:-1]), location_href)
            else:
                if RPMProxy.is_rpm_file(package_name) and not RPMProxy.is_debuginfo_rpm(package_name):
                    rs[package_name] = os.path.join('/'.join(package_path.split('/')[:-1]), location_href)

        return rs

    def _all_debuginfo_rpm(self, debuginfo_path):
        """

        :param debuginfo_path: debuginfo包所在的子路径
        :return:
        """
        if not debuginfo_path:
            logger.info("debuginfo path not specify")
            return {}

        logger.debug(f"search all debuginfo rpm at {debuginfo_path}")
        return self._prepare_package_info(debuginfo_path, debuginfo=True)

    def _all_focus_on_rpm(self, rpm_path):
        """

        :param path: rpm所在的子路径
        :return:
        """
        if not rpm_path:
            logger.info("rpm package path not specify")
            return {}

        logger.debug(f"search all focus on rpm at {rpm_path}")
        return self._prepare_package_info(rpm_path)

class OBSRepo(OEDistRepo):
    """
    OBS 发布repo
    """
    def __init__(self, path, work_dir, category, arch=None):
        super(OEDistRepo, self).__init__(path, work_dir, category)

        self._raw_path = path
        self.verbose_path = os.path.basename(path)

        self._cmp_type = CMP_TYPE_DIST_REPOSITORY

        #self.upsert_a_group(f"{arch}", f"{arch}", self.find_primary_sqlite_path(f"repodata"))
        #self.upsert_a_group("noarch", "noarch", self.find_primary_sqlite_path(f"repodata"))
        self.upsert_a_group(f"{arch}", f"{arch}")
        self.upsert_a_group("noarch", "noarch")

    def _prepare_package_info(self, package_html_url, debuginfo=False, sqlite=False):
        """
        计算所有需要比对的包
        1. 忽略doc、help等包
        2. 相同的包，取时间最近的
        :return:
        """

        tmp_dir = tempfile.TemporaryDirectory(prefix="obs_dist_repo_", suffix="_Packages", dir=self._work_dir)
        package_html_local = os.path.join(tmp_dir.name, "packages.html")

        if do_download(package_html_url, package_html_local) is None:
            return {}

        rs = {}
        # 解析packages列表
        with open(package_html_local, "r") as f:
            soup = bs(f.read(), 'html.parser')
            for row in soup.select("pre a"):
                # <td><a href=anaconda-33.19-19.oe1.x86_64.rpm></td><td>64.3 KiB</td><td>2021-Apr-01 16:58</td>
                package = row.attrs['href']
                if not package.endswith("rpm"):
                    continue
                # m = re.match("(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\W+(.*)", row.next_sibling.strip())
                # date_part = m.group(1)
                # size = m.group(2)

                if sqlite:
                    rs[package] = package
                    continue

                if debuginfo:
                    if RPMProxy.is_debuginfo_rpm(package):
                        rs[package] = os.path.join(package_html_url, package)
                else:
                    if RPMProxy.is_rpm_file(package) and not RPMProxy.is_debuginfo_rpm(package):
                        rs[package] = os.path.join(package_html_url, package)

        return rs
