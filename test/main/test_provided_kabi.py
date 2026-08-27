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
# Author:
# Create: 2026-08-26
# Description: test extract provided kabi from ko file
# **********************************************************************************
"""
import io
import os
import struct
from unittest import TestCase
from unittest.mock import call, patch

from oecp.kabi.kabi_generate import KabiGenerate

SHT_PROGBITS = 1
SHT_SYMTAB = 2
SHT_STRTAB = 3
STB_GLOBAL = 1
STT_NOTYPE = 0
STB_LOCAL = 0
SHN_ABS = 0xFFF1

ELF_HDR_FMT = '<16sHHLQQQIHHHHHH'
SHDR_FMT = '<IIQQQQIIQQ'
SYM_FMT = '<IBBHQQ'


def pack_sym(st_name, st_info, st_shndx, st_value):
    return struct.pack(SYM_FMT, st_name, (st_info << 4) | STT_NOTYPE, 0, st_shndx, st_value, 0)


def build_elf(mode):
    sec_names = b'\x00.symtab\x00.strtab\x00.rodata\x00.shstrtab\x00'
    sym_names = b'\x00__crc_export_a\x00__crc_export_b\x00__crc_undef_x\x00normal_sym\x00'
    if mode == 'abs':
        symtab = (pack_sym(0, STB_LOCAL, 0, 0) +
                  pack_sym(1, STB_GLOBAL, SHN_ABS, 0x12345678) +
                  pack_sym(16, STB_GLOBAL, SHN_ABS, 0xABCDEF01) +
                  pack_sym(31, STB_GLOBAL, 0, 0) +          # SHN_UNDEF -> must be skipped
                  pack_sym(45, STB_GLOBAL, 3, 0xDEADBEEF))  # normal sym, no __crc_ -> skipped
    else:
        # section-relative: both CRCs at offsets 0 and 4 of .rodata
        symtab = (pack_sym(0, STB_LOCAL, 0, 0) +
                  pack_sym(1, STB_GLOBAL, 3, 0) +
                  pack_sym(16, STB_GLOBAL, 3, 4) +
                  pack_sym(31, STB_GLOBAL, 0, 0) +
                  pack_sym(45, STB_GLOBAL, 3, 8))
    rodata = struct.pack('<II', 0x12345678, 0xABCDEF01)

    e_shoff = 64
    sections_off = e_shoff + 5 * 64
    shstr_off = sections_off
    strtab_off = shstr_off + len(sec_names)
    symtab_off = strtab_off + len(sym_names)
    rodata_off = symtab_off + len(symtab)

    eh = struct.pack(ELF_HDR_FMT, b'\x7fELF' + b'\x02\x01\x01' + b'\x00' * 9,
                     62, 1, 1, 0, 0, e_shoff, 0, 64, 0, 0, 64, 5, 4)

    def shdr(name, sh_type, flags, off, size, link=0, info=0, entsize=0):
        return struct.pack(SHDR_FMT, name, sh_type, flags, 0, off, size, link, info, 0, entsize)

    null = shdr(0, 0, 0, 0, 0)
    s1 = shdr(1, SHT_SYMTAB, 0, symtab_off, len(symtab), link=2, info=1, entsize=24)
    s2 = shdr(9, SHT_STRTAB, 0, strtab_off, len(sym_names))
    s3 = shdr(17, SHT_PROGBITS, 0, rodata_off, len(rodata))
    shstr = shdr(25, SHT_STRTAB, 0, shstr_off, len(sec_names))

    blob = eh + null + s1 + s2 + s3 + shstr
    blob += sec_names + sym_names + symtab + rodata
    return blob


class TestProvidedKabi(TestCase):
    EXPECTED = ['0x12345678\texport_a', '0xabcdef01\texport_b']

    def test_extract_provided_kabi_abs(self):
        self._check_extract('abs')

    def test_extract_provided_kabi_section_rel(self):
        self._check_extract('section_rel')

    def test_merge_provided_kabi_into_main_result(self):
        kabi_dic = {
            '0x00000001': 'kernel_api',
            '0x00000002': 'shared_api',
        }
        path_dic = {
            '0x00000001': 'consumer_a.ko',
            '0x00000002': 'consumer_b.ko',
        }
        provided_dic = {
            '0x00000002': 'shared_api',
            '0x00000003': 'internal_only_api',
        }
        provided_path_dic = {
            '0x00000002': 'provider.ko',
            '0x00000003': 'provider.ko',
        }

        result = KabiGenerate.merge_kabi_result(
            kabi_dic, path_dic, provided_dic, provided_path_dic)

        self.assertEqual(result, (
            ['0x00000001', '0x00000002'],
            ['kernel_api', 'shared_api'],
            ['consumer_a.ko', 'consumer_b.ko;provider.ko'],
            [False, True],
        ))

    @patch('oecp.kabi.kabi_generate.CsvResult')
    def test_generate_writes_only_unified_kabi_result(self, csv_result):
        result_writer = csv_result.return_value
        generator = KabiGenerate(os.path.dirname(__file__), None, None)
        generator.dir_kabi_generate = lambda _: (
            {
                '0x00000001': 'kernel_api',
                '0x00000002': 'shared_api',
            },
            {
                '0x00000001': 'consumer_a.ko',
                '0x00000002': 'consumer_b.ko',
            },
            {
                '0x00000002': 'shared_api',
                '0x00000003': 'not_kabi_api',
            },
            {
                '0x00000002': 'provider.ko',
                '0x00000003': 'provider.ko',
            },
        )
        generator.get_kabiwhite_list = lambda: None
        generator.generate()

        csv_result.assert_called_once_with()
        self.assertEqual(result_writer.create.call_args_list, [
            call('crc', ['0x00000001', '0x00000002']),
            call('driver_kabi', ['kernel_api', 'shared_api']),
            call('is_driver_internal_api', [False, True]),
            call('path', ['consumer_a.ko', 'consumer_b.ko;provider.ko']),
        ])

    def _check_extract(self, mode):
        ko_path = 'test_provided_{}.ko'.format(mode)
        with patch('builtins.open', return_value=io.BytesIO(build_elf(mode))):
            result = sorted(KabiGenerate.extract_provided_kabi(ko_path))

        self.assertEqual(result, self.EXPECTED)
