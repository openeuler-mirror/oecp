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

import logging
import lzma
import os
import re
import struct
import tempfile

from elftools.elf.elffile import ELFFile

from oecp.dumper.base import AbstractDumper
from oecp.kabi.csv_result import CsvResult
from oecp.main.extract_kapi import EXTRACTKAPI
from oecp.proxy.rpm_proxy import RPMProxy
from oecp.utils.shell import shell_cmd

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
                kabi_dic, path_dic, provided_dic, provided_path_dic = self.dir_kabi_generate(self.in_dir)
                crc_list, kabi_list, path_list, internal_api_list = self.merge_kabi_result(
                    kabi_dic, path_dic, provided_dic, provided_path_dic)
                self.result.create("crc", crc_list)
                self.result.create("driver_kabi", kabi_list)
                self.result.create("is_driver_internal_api", internal_api_list)
                self.result.create("path", path_list)
            elif self.in_dir.endswith(".rpm"):
                logger.info("Input is driver rpm file")
                kabi_dic, path_dic, provided_dic, provided_path_dic = self.rpm_kabi_generate(self.in_dir)
                crc_list, kabi_list, path_list, internal_api_list = self.merge_kabi_result(
                    kabi_dic, path_dic, provided_dic, provided_path_dic)
                self.result.create("crc", crc_list)
                self.result.create("driver_kabi", kabi_list)
                self.result.create("is_driver_internal_api", internal_api_list)
                self.result.create("path", path_list)
            else:
                logger.info("Input is kabi_list file")
                try:
                    with open(self.in_dir, "r") as f:
                        for line in f:
                            kabi_list.append(line.strip())
                except Exception as e:
                    logger.error("Failed to read kabi_list file: %s, error: %s", self.in_dir, e)
                    raise ValueError(f"Failed to read kabi_list file: {self.in_dir}") from e
                self.result.create("kabi", kabi_list)
                self.result.create("is_driver_internal_api", [False] * len(kabi_list))

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
        provided_set = set()
        source_map = {}
        provided_source_map = {}

        for root, _, files in os.walk(driver_dir):
            for file in files:
                file_path = os.path.join(root, file)
                display = self._display_path(os.path.relpath(file_path, driver_dir))
                if file.endswith('.rpm'):
                    logger.info(f"Processing RPM file: {file_path}")
                    lines, sources, provided, provided_sources = self.extract_kabi_from_rpm(file_path, display)
                elif file.endswith(('.ko', '.ko.xz')):
                    logger.info(f"Processing .ko file: {file_path}")
                    lines = self.extract_kabi(file_path)
                    sources = {line: [display] for line in lines}
                    provided = self.extract_provided_kabi(file_path)
                    provided_sources = {line: [display] for line in provided}
                else:
                    continue
                kabi_set.update(lines)
                provided_set.update(provided)
                for line, paths in sources.items():
                    source_map.setdefault(line, []).extend(paths)
                for line, paths in provided_sources.items():
                    provided_source_map.setdefault(line, []).extend(paths)

        dict_kabi = self.component_kabi(kabi_set)
        path_dic = self._kabi_paths(kabi_set, source_map)
        provided_dic = self.component_kabi(provided_set)
        provided_path_dic = self._kabi_paths(provided_set, provided_source_map)
        return dict_kabi, path_dic, provided_dic, provided_path_dic

    def rpm_kabi_generate(self, rpm_file):
        kabi_set = set()
        provided_set = set()
        source_map = {}
        provided_source_map = {}
        display = os.path.basename(rpm_file)
        lines, sources, provided, provided_sources = self.extract_kabi_from_rpm(rpm_file, display)
        kabi_set.update(lines)
        provided_set.update(provided)
        for line, paths in sources.items():
            source_map.setdefault(line, []).extend(paths)
        for line, paths in provided_sources.items():
            provided_source_map.setdefault(line, []).extend(paths)

        dict_kabi = self.component_kabi(kabi_set)
        path_dic = self._kabi_paths(kabi_set, source_map)
        provided_dic = self.component_kabi(provided_set)
        provided_path_dic = self._kabi_paths(provided_set, provided_source_map)

        return dict_kabi, path_dic, provided_dic, provided_path_dic

    @staticmethod
    def _display_path(rel_path):
        rel_path = rel_path.replace(os.sep, "/")
        while rel_path.startswith("./"):
            rel_path = rel_path[2:]
        return rel_path

    @staticmethod
    def _kabi_paths(kabi_set, source_map):
        # aggregate source paths per CRC, a line may come from several .ko files
        path_dic = {}
        for line in kabi_set:
            parts = line.split()
            if len(parts) < 2:
                continue
            paths = path_dic.setdefault(parts[0], [])
            for path in source_map.get(line, []):
                if path not in paths:
                    paths.append(path)
        return {crc: ";".join(paths) for crc, paths in path_dic.items()}

    @staticmethod
    def component_kabi(kabi_symbols):
        kabi_dic = {}
        for item in kabi_symbols:
            parts = item.split()
            kabi_dic[parts[0]] = parts[1]
        sorted_kabi_dic = {k: v for k, v in sorted(kabi_dic.items(), key=lambda item: item[1])}

        return sorted_kabi_dic

    @staticmethod
    def merge_kabi_result(kabi_dic, path_dic, provided_dic, provided_path_dic):
        """
        Mark required KABI symbols that can be provided by the input drivers.

        A symbol is a driver-internal API when the same CRC and symbol name are
        exported by one of the input driver modules. Exported symbols that are
        not in the required KABI set are omitted. Paths from consumers and
        matching providers are kept on the same result row without duplication.
        :return: Parallel lists of CRCs, symbols, paths, and internal-API flags.
        """
        kabi_items = set(kabi_dic.items())
        internal_api_items = kabi_items & set(provided_dic.items())
        sorted_items = sorted(kabi_items, key=lambda item: (item[1], item[0]))

        crc_list = []
        kabi_list = []
        path_list = []
        internal_api_list = []
        for crc, symbol in sorted_items:
            crc_list.append(crc)
            kabi_list.append(symbol)
            path_list.append(KabiGenerate._merge_paths(path_dic.get(crc, ""),
                                                        provided_path_dic.get(crc, "")
                                                        if (crc, symbol) in internal_api_items else ""))
            internal_api_list.append((crc, symbol) in internal_api_items)

        return crc_list, kabi_list, path_list, internal_api_list

    @staticmethod
    def _merge_paths(*path_values):
        paths = []
        for path_value in path_values:
            for path in path_value.split(";"):
                if path and path not in paths:
                    paths.append(path)
        return ";".join(paths)

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

    def extract_kabi_from_rpm(self, rpm_file, display_prefix=""):
        """
        Extract kabi  from an RPM package.
        :param display_prefix: display name of the rpm, used to build the ko path column
        :return: (Set of dependent KABI symbols, dict of dependent line -> source ko paths,
                  Set of provided KABI symbols, dict of provided line -> source ko paths)
        """
        extracted_kabi = set()
        source_map = {}
        extracted_provided = set()
        provided_source_map = {}
        try:
            # chdir to temp dir breaks relative paths, resolve to absolute first
            rpm_file = os.path.abspath(rpm_file)
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
                            ko_display = self._display_path(extracted_ko_path)
                            if display_prefix:
                                ko_display = f"{display_prefix}:{ko_display}"
                            lines = self.extract_kabi(extracted_ko_path)
                            extracted_kabi.update(lines)
                            for line in lines:
                                source_map.setdefault(line, []).append(ko_display)
                            provided = self.extract_provided_kabi(extracted_ko_path)
                            extracted_provided.update(provided)
                            for line in provided:
                                provided_source_map.setdefault(line, []).append(ko_display)
                # Switch back to the original directory
                os.chdir(current_dir)
                logger.info("Switched back to original directory: %s", current_dir)
        except Exception as e:
            logger.error("Error extracting .ko files from %s: %s", rpm_file, e)
        return extracted_kabi, source_map, extracted_provided, provided_source_map

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
                # modprobe cannot handle variable-length __versions entries
                if "Invalid argument" in err:
                    return KabiGenerate.extract_kabi_variable_length(ko_path)
                return set()
        except Exception as e:
            logger.error(f"Error extracting KABI from {ko_path}: {e}")
            return set()

    @staticmethod
    def extract_kabi_variable_length(ko_path):
        """
        Extract KABI information from a .ko/.ko.xz file by parsing the variable-length
        __versions section entries (little-endian next_offset + crc + null-terminated name).
        :param ko_path: Path to the .ko or .ko.xz file
        :return: Set of KABI symbols in '0x<crc>\t<name>' format.
        """
        kabi_set = set()
        try:
            opener = lzma.open if ko_path.endswith('.xz') else open
            with opener(ko_path, 'rb') as f:
                elf = ELFFile(f)
                sec = elf.get_section_by_name('__versions')
                if not sec:
                    logger.warning(f"No __versions section in {ko_path}")
                    return kabi_set
                data = sec.data()

            offset = 0
            while offset + 8 <= len(data):
                next_off, crc = struct.unpack_from('<II', data, offset)
                if next_off == 0:
                    break
                name_start = offset + 8
                name_end = data.find(b'\x00', name_start)
                if name_end == -1:
                    break
                name = data[name_start:name_end].decode('ascii', errors='replace')
                kabi_set.add(f"0x{crc:08x}\t{name}")
                offset += next_off
        except Exception as e:
            logger.error(f"Error extracting KABI from {ko_path}: {e}")
        return kabi_set

    @staticmethod
    def extract_provided_kabi(ko_path):
        """
        Extract KABI symbols provided (exported) by a .ko file by parsing
        the __crc_* symbols in the ELF symbol table with pyelftools.
        :param ko_path: Path to the .ko or .ko.xz file
        :return: Set of provided KABI symbols in '0x<crc>\t<name>' format.
        """
        kabi_set = set()
        try:
            opener = lzma.open if ko_path.endswith('.xz') else open
            with opener(ko_path, 'rb') as f:
                elf = ELFFile(f)
                symtab = elf.get_section_by_name('.symtab')
                if not symtab:
                    logger.warning(f"No .symtab section in {ko_path}")
                    return kabi_set
                for symbol in symtab.iter_symbols():
                    name = symbol.name
                    if not name.startswith('__crc_') or symbol.entry['st_shndx'] == 'SHN_UNDEF':
                        continue
                    crc = KabiGenerate._symbol_crc(elf, symbol)
                    if crc is not None:
                        kabi_set.add(f"0x{crc:08x}\t{name[len('__crc_'):]}")
        except Exception as e:
            logger.error(f"Error extracting provided KABI from {ko_path}: {e}")
        return kabi_set

    @staticmethod
    def _symbol_crc(elf, symbol):
        # old kernels keep the CRC as an absolute symbol value, newer kernels
        # store it as u32 data in the section the __crc_* symbol points to
        shndx = symbol.entry['st_shndx']
        if shndx == 'SHN_ABS':
            return symbol.entry['st_value'] & 0xFFFFFFFF
        if isinstance(shndx, int):
            data = elf.get_section(shndx).data()
            offset = symbol.entry['st_value']
            if offset + 4 <= len(data):
                fmt = '<I' if elf.little_endian else '>I'
                return struct.unpack_from(fmt, data, offset)[0]
        return None

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
                kb_kabi_set = {line.strip() for line in file}
        except FileNotFoundError:
            logger.error(f"File not found: {kb_dir}")
            return []
        except Exception as e:
            logger.error(f"Error reading file {kb_dir}: {e}")
            return []

        results = [symbol in kb_kabi_set for symbol in kabi_symbols]
        return results
