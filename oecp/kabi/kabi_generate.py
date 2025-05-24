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
import re
import logging
import tempfile

from oecp.dumper.base import AbstractDumper
from oecp.utils.shell import shell_cmd
from oecp.kabi.csv_result import CsvResult
from oecp.proxy.rpm_proxy import RPMProxy
from oecp.main.extract_kapi import EXTRACTKAPI


logger = logging.getLogger("oecp")


class KabiGenerate:
    def __init__(self, in_dir, branch, arch, src_kpath=None):
        self.in_dir = in_dir
        self.branch = branch
        self.arch = arch
        self.src_kpath = src_kpath
        self.result = CsvResult()

    def generate(self):
        """
        Generate KABI and KAPI lists based on input directory, kabi whitelist directory, and kernel source path.
        :param self: Instance of KabiGenerate
        """

        if os.path.exists(self.in_dir):
            kabi_list = []

            if os.path.isdir(self.in_dir):
                logger.info("Input is directory, start kabi generating")
                kabi_dic = self.dir_kabi_generate(self.in_dir)
                crc_list = list(kabi_dic.keys())
                kabi_list = list(kabi_dic.values())
                self.result.create("crc", crc_list)
                self.result.create("driver_kabi", kabi_list)
            elif self.in_dir.endswith(".rpm"):
                logger.info("Input is driver rpm file")
                kabi_dic = self.rpm_kabi_generate(self.in_dir)
                kabi_list = list(kabi_dic.values())
                self.result.create("crc", list(kabi_dic.keys()))
                self.result.create("driver_kabi", kabi_list)
            else:
                logger.info("Input is kabi_list file")
                try:
                    with open(self.in_dir, "r") as f:
                        for line in f.readlines():
                            kabi_list.append(line.strip())
                except Exception as e:
                    logger.error("Failed to read kabi_list file: %s, error: %s", self.in_dir, e)
                    raise UnicodeDecodeError from e
                self.result.create("kabi", kabi_list)

            if self.src_kpath:
                logger.info("Kernel source directory is provided, start kapi generating")
                kapi_dic = self.kapi_generate(kabi_list, self.src_kpath)
                self.result.create("kapi", [kapi_dic[key] for key in kabi_list])

            kabi_whitelist = self.get_kabiwhite_list()
            if kabi_whitelist:
                logger.info("Kabi whitelist directory is provided, start comparing")
                judgment_list = self.is_kabi_whitelist(kabi_list, kabi_whitelist)
                self.result.create("is_kabi_whitelist", judgment_list)
        else:
            logger.error(f"The {self.in_dir} does not exist.")

    def dir_kabi_generate(self, driver_dir):
        """
        Generate KABI list from .ko files, RPM packages, or .ko.xz files in the specified directory.
        :param driver_dir: Directory containing .ko files, RPM packages, or .ko.xz files.
        """
        kabi_set = set()

        for root, _, files in os.walk(driver_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if file.endswith('.rpm'):
                    logger.info(f"Processing RPM file: {file_path}")
                    kabi_set.update(self.extract_kabi_from_rpm(file_path))
                elif file.endswith('.ko') or file.endswith('.ko.xz'):
                    logger.info(f"Processing .ko file: {file_path}")
                    kabi_set.update(self.extract_kabi(file_path))

        dict_kabi = self.component_kabi(kabi_set)
        return dict_kabi

    def rpm_kabi_generate(self, rpm_file):
        kabi_set = set()
        kabi_set.update(self.extract_kabi_from_rpm(rpm_file))

        dict_kabi = self.component_kabi(kabi_set)

        return dict_kabi

    @staticmethod
    def component_kabi(kabi_symbols):
        kabi_dic = {}
        for item in kabi_symbols:
            parts = item.split()
            kabi_dic[parts[0]] = parts[1]
        sorted_kabi_dic = {k: v for k, v in sorted(kabi_dic.items(), key=lambda item: item[1])}

        return sorted_kabi_dic


    @staticmethod
    def kapi_generate(kabi_symbols, src_kpath):
        """
        :param kabi_symbols: list of kabi
        :param src_kpath: kernel source path
        """
        current_dir = os.getcwd()
        src_obj = RPMProxy.uncompress_source_rpm(src_kpath)
        extract = EXTRACTKAPI()
        results = extract.multithread_get_prototype(kabi_symbols, src_obj)
        os.chdir(current_dir)
        return results

    def get_kabiwhite_list(self):
        dir_kabi_whitelist = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                          "conf/kabi_whitelist")
        if self.branch and self.arch:
            branch = AbstractDumper.get_branch_dir(dir_kabi_whitelist, self.branch)
            kb_dir = os.path.join(dir_kabi_whitelist, branch, self.arch)
            if os.path.exists(kb_dir):
                logger.debug("Get correct kabi_whitelist: %s", kb_dir)
                return kb_dir
        logger.warning("Not input branch and arch of kabi whitelist.")
        return None

    def extract_kabi_from_rpm(self, rpm_file):
        """
        Extract kabi  from an RPM package.
        :return: Set of KABI symbols
        """
        extracted_kabi = set()
        try:
            with tempfile.TemporaryDirectory(suffix='__srpm__', dir='/tmp') as temp_dir:
                logger.info(f"Created temporary directory: {temp_dir}")
                current_dir = os.getcwd()
                os.chdir(temp_dir)
                logger.info(f"Current working directory: {os.getcwd()}")
                logger.info(f"Extracting {rpm_file}")
                RPMProxy.perform_cpio(rpm_file)
                rpm_name = os.path.basename(rpm_file)
                root_dir = "./usr/local/Ascend/driver/host_rpm/" if re.match("ascend-hdk", rpm_name.lower()) else "."
                # Extract RPM contents
                for root, _, files in os.walk(root_dir):
                    for file_info in files:
                        if file_info.endswith(('.ko', '.ko.new', '.ko.xz')):
                            extracted_ko_path = os.path.join(root, file_info)
                            extracted_kabi.update(self.extract_kabi(extracted_ko_path))
                # Switch back to the original directory
                os.chdir(current_dir)
                logger.info("Switched back to original directory: %s", current_dir)
        except Exception as e:
            logger.error("Error extracting .ko files from %s: %s", rpm_file, e)
        return extracted_kabi

    @staticmethod
    def extract_kabi(ko_path):
        """
        Extract KABI information from a .ko file using modprobe --dump-modversions.
        :return: Set of KABI symbols.
        """
        try:
            ret, out, err = shell_cmd(['modprobe', '--dump-modversions', ko_path])
            if ret == 0:
                return set(out.splitlines())
            else:
                logger.error(f"Failed to extract KABI from {ko_path}: {err}")
                return set()
        except Exception as e:
            logger.error(f"Error extracting KABI from {ko_path}: {e}")
            return set()

    @staticmethod
    def is_kabi_whitelist(kabi_symbols, kb_dir):
        """
        Check if each KABI symbol in kabi_symbols is in the whitelist.
        :param kabi_symbols: List of KABI entries
        :param kb_dir: Path to the file containing KABI whitelist entries
        :return: List of booleans indicating whether each KABI symbol is in the whitelist
        """
        if not isinstance(kabi_symbols, list):
            logger.error("Invalid input type for kabi_symbols. Expected a list.")
            return []

        try:
            with open(kb_dir, 'r', encoding='utf-8') as file:
                kb_kabi_set = set(line.strip() for line in file)
        except FileNotFoundError:
            logger.error(f"File not found: {kb_dir}")
            return []
        except Exception as e:
            logger.error(f"Error reading file {kb_dir}: {e}")
            return []

        results = [symbol in kb_kabi_set for symbol in kabi_symbols]
        return results
