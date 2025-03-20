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
from datetime import datetime, timezone

from oecp.utils.shell import shell_cmd
from oecp.kabi.csv_result import CsvResult
from oecp.proxy.rpm_proxy import RPMProxy
from oecp.main.extract_kapi import EXTRACTKAPI


logger = logging.getLogger("oecp")


class KabiGenerate:
    def __init__(self, in_dir, kb_dir=None, src_kpath=None):
        self.in_dir = in_dir
        self.kb_dir = kb_dir
        self.src_kpath = src_kpath
        csv_name = f"result-{datetime.now(tz=timezone.utc)}.csv"
        self.result = CsvResult(f"/tmp/kabi/{csv_name}")

    def generate(self):
        """
        Generate KABI and KAPI lists based on input directory, kabi whitelist directory, and kernel source path.
        :param self: Instance of KabiGenerate
        """
        if not os.path.exists("/tmp/kabi"):
            os.makedirs("/tmp/kabi")

        if os.path.exists(self.in_dir):
            kabi_list = []

            if os.path.isdir(self.in_dir):
                logger.info("Input is directory, start kabi generating")
                kabi_dic = self.kabi_generate(self.in_dir)
                crc_list = list(kabi_dic.keys())
                kabi_list = list(kabi_dic.values())
                self.result.create("crc", crc_list)
                self.result.create("driver_kabi", kabi_list)
            else:
                logger.info("Input is kabi_list file")
                with open(self.in_dir, "r") as f:
                    for line in f.readlines():
                        kabi_list.append(line.strip())
                self.result.create("kabi", kabi_list)

            if self.src_kpath:
                logger.info("Kernel source directory is provided, start kapi generating")
                kapi_dic = self.kapi_generate(kabi_list, self.src_kpath)
                self.result.create("kapi", [kapi_dic[key] for key in kabi_list])

            if self.kb_dir:
                logger.info("Kabi whitelist directory is provided, start comparing")
                judgment_list = self.is_kabi_whitelist(kabi_list, self.kb_dir)
                self.result.create("is_kabi_whitelist", judgment_list)
        else:
            logger.error(f"The {self.in_dir} does not exist.")

    def kabi_generate(self, driver_dir):
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

        kabi_dic = {}
        for item in kabi_set:
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
        results = extract.multi_get_prototype(kabi_symbols, src_obj)
        os.chdir(current_dir)
        return results

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
                logger.info(f"Switched back to original directory: {current_dir}")
        except Exception as e:
            logger.error(f"Error extracting .ko files from {rpm_file}: {e}")
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
