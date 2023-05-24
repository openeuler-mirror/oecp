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
# **********************************************************************************
"""

import os
import logging
import tempfile
import magic

from pathlib import Path
from oecp.proxy.rpm_proxy import RPMProxy
from oecp.dumper.base import AbstractDumper

logger = logging.getLogger('oecp')


class RPMExtractDumper(AbstractDumper):

    def __init__(self, repository, cache=None, config=None):
        super(RPMExtractDumper, self).__init__(repository, cache, config)
        _path = os.path.basename(os.path.basename(__file__)).split('.')[0]
        self._work_dir = self.repository.work_dir
        self._extract_info = {}

        # 文件类型
        self._text_mime = ["text/plain"]
        self._library_mime = ["application/x-sharedlib", "application/x-pie-executable"]
        self._archive_mime = ["application/x-archive"]
        self._head_mime = ["text/x-c"]

        # 保存解压目录到对应类型文件列表的映射
        self._config_files = {}
        self._library_files = {}
        self._service_files = {}
        self._header_files = {}
        self._cmd_files = {}

    def do_rpm_cpio(self, rpm_path):
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
        self._collect_library_files(extract_dir_name)
        self._collect_service_files(extract_dir_name)
        self._collect_header_files(extract_dir_name)
        self._collect_cmd_files(extract_dir_name)

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

    def _collect_library_files(self, extract_dir_name):
        link_so_file = extract_dir_name + "_linkfile"
        if 'debuginfo' in extract_dir_name:
            return
        extract_path_obj = Path(extract_dir_name)
        all_share_files = [extract_path_obj.glob('lib/**/*'), extract_path_obj.glob('lib64/**/*'),
                    extract_path_obj.glob('usr/lib/**/*'), extract_path_obj.glob('usr/lib64/**/*'),
                    extract_path_obj.glob('**/*.a')]
        self._library_files.setdefault(extract_dir_name, [])
        self._library_files.setdefault(link_so_file, [])
        for glob in all_share_files:
            for file in glob:
                if file.is_file():
                    file_path = file.as_posix()
                    file_type = magic.from_file(file_path, mime=True)
                    if file_type in self._library_mime and ".so" in file_path:
                        self._library_files.setdefault(extract_dir_name, []).append(file_path)
                    elif file_type in self._archive_mime:
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
                    self._cmd_files.setdefault(extract_dir_name, []).append(file.as_posix())

    def get_extract_info(self):
        return self._extract_info

    def get_config_files(self, extract_dir_name):
        return self._config_files[extract_dir_name]

    def get_library_files(self, extract_dir_name):
        return self._library_files.get(extract_dir_name)

    def get_service_files(self, extract_dir_name):
        return self._service_files[extract_dir_name]

    def get_header_files(self, extract_dir_name):
        return self._header_files[extract_dir_name]

    def get_cmd_files(self, extract_dir_name):
        return self._cmd_files[extract_dir_name]

    def get_package_extract_path(self, kernel_name_version):
        for k, v in self._extract_info.items():
            name, version = RPMProxy.rpm_name_version(k)
            rpm_name_version = name + version
            if rpm_name_version != kernel_name_version:
                continue
            else:
                extract_path = str(v.name)
                return extract_path
        return ''

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
