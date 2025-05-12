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
# **********************************************************************************
"""
import json
import os
import logging
import tempfile
import magic

from pathlib import Path
from oecp.proxy.rpm_proxy import RPMProxy
from oecp.dumper.base import AbstractDumper
from oecp.utils import common

logger = logging.getLogger('oecp')


class RPMExtractDumper(AbstractDumper):

    def __init__(self, repository, cache=None, config=None):
        super(RPMExtractDumper, self).__init__(repository, cache, config)
        _path = os.path.basename(os.path.basename(__file__)).split('.')[0]
        self._work_dir = self.repository.work_dir
        self._extract_info = {}
        self.kabi_white_list = []
        self.drive_kabi_white_list = []
        self.link_flag = "_[link]_"

        # 文件类型
        self._text_mime = ["text/plain"]
        self._library_mime = ["application/x-sharedlib", "application/x-pie-executable"]
        self._head_mime = ["text/x-c", "text/x-c++"]
        self._ko_mime = ["application/x-object", "application/x-xz"]

        # 保存解压目录到对应类型文件列表的映射
        self._config_files = {}
        self._jar_files = {}
        self._library_files = {}
        self._service_files = {}
        self._header_files = {}
        self._cmd_files = {}
        self._symbol_files = {}
        self._ko_files = {}

    def do_rpm_cpio(self, rpm_path):
        try:
            full_path = os.path.realpath(rpm_path)
            pwd_path = os.getcwd()
            verbose_path = os.path.basename(rpm_path)
            extract_dir_obj = tempfile.TemporaryDirectory(suffix='__rpm__', prefix=f'_{verbose_path}_',
                                                          dir=self._work_dir)
            extract_dir_name = extract_dir_obj.name
            os.chdir(extract_dir_name)
            RPMProxy.perform_cpio(full_path)
            os.chdir(pwd_path)
            self._extract_info.setdefault(verbose_path, extract_dir_obj)
            self._collect_config_file(extract_dir_name)
            self._collect_jar_files(extract_dir_name)
            self._collect_library_files(extract_dir_name)
            self._collect_service_files(extract_dir_name)
            self._collect_header_files(extract_dir_name)
            self._collect_cmd_files(extract_dir_name)
            self._collect_ko_files(extract_dir_name, verbose_path)
            self._collect_symbol_files(extract_dir_name)
            if not self.kabi_white_list and not self.drive_kabi_white_list:
                self.load_white_list()
        except Exception as err:
            logger.exception(f"Collect files error: {err}")

    def clean(self):
        # clean tempfile
        for rpm_dir in self._extract_info:
            self._extract_info[rpm_dir] = None

    def _collect_config_file(self, extract_dir_name):
        extract_path_obj = Path(extract_dir_name)
        all_files = extract_path_obj.glob('etc/**/*.conf')
        self._config_files.setdefault(extract_dir_name, [])
        for file in all_files:
            if file.is_file():
                file_path = file.as_posix()
                file_type = magic.from_file(file_path, mime=True)
                if file_type in self._text_mime:
                    self._config_files.setdefault(extract_dir_name, []).append(file_path)

    def _collect_jar_files(self, extract_dir_name):
        extract_path_obj = Path(extract_dir_name)
        all_files = extract_path_obj.glob('**/*.jar')
        self._jar_files.setdefault(extract_dir_name, [])
        for file in all_files:
            if file.is_file():
                self._jar_files.setdefault(extract_dir_name, []).append(file.as_posix())

    def _collect_library_files(self, extract_dir_name):
        link_so_file = extract_dir_name + "_linkfile"
        if 'debuginfo' in extract_dir_name:
            return
        extract_path_obj = Path(extract_dir_name)
        all_files = [extract_path_obj.glob('lib/**/*'), extract_path_obj.glob('lib64/**/*'),
                     extract_path_obj.glob('usr/lib/**/*'), extract_path_obj.glob('usr/lib64/**/*')]
        self._library_files.setdefault(extract_dir_name, [])
        self._library_files.setdefault(link_so_file, [])
        for glob in all_files:
            for file in glob:
                if file.is_file():
                    file_path = file.as_posix()
                    file_type = magic.from_file(file_path, mime=True)
                    if file_type in self._library_mime and ".so" in file_path:
                        self._library_files.setdefault(extract_dir_name, []).append(file_path)
                elif os.path.islink(file.as_posix()):
                    link_file_name = os.readlink(file.as_posix())
                    if link_file_name.endswith(".so") or ".so." in link_file_name:
                        self._library_files.setdefault(link_so_file, []).append(
                            [os.path.basename(file.as_posix()), link_file_name])

    def _collect_service_files(self, extract_dir_name):
        extract_path_obj = Path(extract_dir_name)
        all_files = extract_path_obj.glob('usr/lib/systemd/system/**/*.service')
        self._service_files.setdefault(extract_dir_name, [])
        for file in all_files:
            if file.is_file():
                self._service_files.setdefault(extract_dir_name, []).append(file.as_posix())

    def _collect_header_files(self, extract_dir_name):
        extract_path_obj = Path(extract_dir_name)
        all_files = extract_path_obj.glob('**/*.h')
        self._header_files.setdefault(extract_dir_name, [])
        for file in all_files:
            if file.is_file():
                file_path = file.as_posix()
                file_type = magic.from_file(file_path, mime=True)
                if file_type in self._head_mime:
                    self._header_files.setdefault(extract_dir_name, []).append(file_path)

    def _collect_cmd_files(self, extract_dir_name):
        extract_path_obj = Path(extract_dir_name)
        all_files = [extract_path_obj.glob('usr/bin/**/*'), extract_path_obj.glob('usr/sbin/**/*'),
                     extract_path_obj.glob('usr/local/bin/**/*'), extract_path_obj.glob('usr/local/sbin/**/*')]
        self._cmd_files.setdefault(extract_dir_name, [])
        for glob in all_files:
            for file in glob:
                if file.is_file():
                    if os.path.islink(file.as_posix()):
                        link_tar = os.readlink(file.as_posix())
                        file_path = ''.join([file.as_posix(), self.link_flag, link_tar])
                    else:
                        file_path = file.as_posix()
                    self._cmd_files.setdefault(extract_dir_name, []).append(file_path)

    def _collect_symbol_files(self, extract_dir_name):
        symbol_files = common.search_elf_files(extract_dir_name)
        self._symbol_files.setdefault(extract_dir_name, symbol_files)

    def _collect_ko_files(self, extract_dir_name, rpm_name):
        extract_path_obj = Path(extract_dir_name)
        if "dkms" in rpm_name:
            cmd = f"cd {extract_path_obj} && find . -name *.tar.gz | xargs -r tar -xf"
            os.system(cmd)
        all_files = extract_path_obj.glob('**/*.ko*')
        self._ko_files.setdefault(extract_dir_name, [])
        for file in all_files:
            if not file.is_file():
                continue
            file_path = file.as_posix()
            file_type = magic.from_file(file_path, mime=True)
            if file_type not in self._ko_mime:
                continue
            self._ko_files.setdefault(extract_dir_name, []).append(file_path)

    def get_extract_info(self):
        return self._extract_info

    def get_config_files(self, extract_dir_name):
        return self._config_files[extract_dir_name]

    def get_jar_files(self, extract_dir_name):
        return self._jar_files[extract_dir_name]

    def get_library_files(self, extract_dir_name):
        return self._library_files.get(extract_dir_name)

    def get_service_files(self, extract_dir_name):
        return self._service_files[extract_dir_name]

    def get_header_files(self, extract_dir_name):
        return self._header_files[extract_dir_name]

    def get_cmd_files(self, extract_dir_name):
        return self._cmd_files[extract_dir_name]

    def get_symbol_files(self, extract_dir_name):
        return self._symbol_files[extract_dir_name]

    def get_ko_files(self, extract_dir_name):
        return self._ko_files[extract_dir_name]

    def get_kabi_white_list(self):
        return self.kabi_white_list

    def get_drive_kabi_white_list(self):
        return self.drive_kabi_white_list

    def get_package_extract_path(self):
        kernel_paths = []
        for package in ['kernel', 'kernel-core']:
            name = RPMProxy.rpm_name(package)

            for k, v in self._extract_info.items():
                if RPMProxy.rpm_name(k) == name:
                    kernel_paths.append(str(v.name))

        return kernel_paths

    def get_branch_dir(self, dir_kabi_whitelist, white_branch):
        with open(os.path.join(dir_kabi_whitelist, "white_list_branch.json"), "r") as jf:
            branch_mapping = json.load(jf)

        for branch_dir, all_branchs in branch_mapping.items():
            if white_branch in all_branchs:
                return branch_dir

        return None

    def open_the_whitelist(self, kabi_whitelist, white_list):
        try:
            with open(kabi_whitelist, "r") as f:
                for line in f.readlines()[1:]:
                    white_list.append(line.strip().replace("\n", ""))
        except FileNotFoundError as err:
            logger.debug("Kabi whitelist %s not exist, Please check whether the arch in (x86_64, aarch64), error: %s",
                         kabi_whitelist, err)

    def load_white_list(self):
        white_branch = self.config.get('white_list').upper()
        arch = self.config.get('arch')
        if arch:
            dir_kabi_whitelist = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                          "conf/kabi_whitelist")
            branch_dir = self.get_branch_dir(dir_kabi_whitelist, white_branch)
            if branch_dir:
                kabi_whitelist_path = os.path.join(dir_kabi_whitelist, branch_dir, arch)
                self.open_the_whitelist(kabi_whitelist_path, self.kabi_white_list)
            else:
                logger.debug("The branch name %s not have kabi whitelist, (Only in: 20.03-LTS-SP1, 20.03-LTS-SP2, "
                             "20.03-LTS-SP3, 22.03-LTS, 22.03-LTS-SP1, 22.03-LTS-SP2)", white_branch)
            kabi_whitelist_path = os.path.join(dir_kabi_whitelist, arch + "_drive_kabi")
            self.open_the_whitelist(kabi_whitelist_path, self.drive_kabi_white_list)
        else:
            logger.debug("Not get arch in (x86_64 or aarch64), so not get the (driver) kabi whitelist.")

    def dump(self, repository):
        path = repository['path']
        debug_info_path = repository['debuginfo_path']
        for rpm_path in [path, debug_info_path]:
            if rpm_path:
                self.do_rpm_cpio(rpm_path)
        return self

    def run(self):
        dumper_list = []
        for _, repository in self.repository.items():
            dumper = self.dump(repository)
            dumper_list.append(dumper)
        return dumper_list
