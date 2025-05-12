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
import logging
import os
import re
from subprocess import TimeoutExpired

from oecp.executor.base import CompareExecutor
from oecp.proxy.rpm_proxy import RPMProxy
from oecp.result.compare_result import CompareResultComposite, CompareResultComponent
from oecp.result.constants import CMP_RESULT_SAME, CMP_TYPE_RPM, CMP_TYPE_RPM_SYMBOL, CMP_RESULT_DIFF, \
    SYMBOL_TYPE, CMP_RESULT_LESS, BRANCH_NAME, DB_PASSWORD, CHANGE_FUN, CHANGE_VAR, REMOVED_DEFINED
from oecp.symbol_analyze.controller.symbol_analyze import RpmController
from oecp.utils.shell import shell_cmd

logger = logging.getLogger('oecp')


class SymbolCompareExecutor(CompareExecutor):

    def __init__(self, dump_a, dump_b, config):
        super(SymbolCompareExecutor, self).__init__(dump_a, dump_b, config)
        self.dump_a = dump_a.run()
        self.dump_b = dump_b.run()
        self._work_dir = self.config.get('detail_path')
        self.rpm_controller = RpmController(config[BRANCH_NAME], config[DB_PASSWORD])

    @staticmethod
    def _extract_deubginfo_changed_fns(content):
        changed_fns = []
        pattern = r"\[C]'(.*)\s(.*)\((.*)at(.*?)changes:"
        all_match = re.finditer(pattern, content)
        for match in all_match:
            if match:
                func = match.group(2).split("::")[-1]
                func = func.replace("=", '')
                changed_fns.append(func)
        return changed_fns

    @staticmethod
    def _extract_debuginfo_symbol(content, mold):
        result = []
        cont_pattern = r'' + mold + '?:\n{2}(.*?)\n{2}'
        all_match = re.finditer(cont_pattern, content, flags=re.S)
        for match in all_match:
            if match:
                for line in match.group(1).split('\n'):
                    if line:
                        sym_pattern = r"{(.*)}"
                        symbol = re.search(sym_pattern, line)
                        if symbol:
                            result.append(symbol.group(1))
        return result

    @staticmethod
    def _extract_deubginfo_changed_var(content):
        result = []
        cont_pattern = r'' + CHANGE_VAR + '?:\n{2}(.*?)\n{3}'
        all_match = re.finditer(cont_pattern, content, flags=re.S)
        for match in all_match:
            if match:
                for line in match.group(1).split('\n'):
                    if line:
                        sym_pattern = r"[C](.*)\' was changed"
                        re_result = re.search(sym_pattern, line)
                        if re_result:
                            symbol = re_result.group(1).split()[-1]
                            result.append(symbol.split('[')[0])
        return result

    @staticmethod
    def _extract_nodebuginfo_symbol(content, mold):
        result = []
        cont_pattern = r'' + mold + '? symbols? not referenced by debug info:\n{2}(.*?)\n{2}'
        all_match = re.finditer(cont_pattern, content, flags=re.S)
        for match in all_match:
            if match:
                for line in match.group(1).split('\n'):
                    if line:
                        symbol = line.strip().split(',')[0]
                        if ' ' in symbol:
                            symbol = symbol.split(' ')[-1]
                        elif '@@' in symbol:
                            symbol = symbol.split('@@')[0]
                        result.append(symbol)

        return result

    def _extract_changed_abi(self, string_content):
        symbol_result = {}
        for mold in SYMBOL_TYPE:
            if mold == CHANGE_FUN:
                one_type_result = self._extract_deubginfo_changed_fns(string_content)
            elif mold == CHANGE_VAR:
                one_type_result = self._extract_deubginfo_changed_var(string_content)
            else:
                one_type_debuginfo_result = self._extract_debuginfo_symbol(string_content, mold)
                one_type_nodebuginfo_result = self._extract_nodebuginfo_symbol(string_content, mold)
                one_type_result = one_type_debuginfo_result + one_type_nodebuginfo_result
            if one_type_result:
                symbol_result.setdefault(mold, one_type_result)

        return symbol_result

    def _get_relative_path(self, files):
        result = []
        for file in files:
            result.append(file.split(self.split_flag)[-1])
        return result

    @staticmethod
    def _get_file_name(file):
        full_name = os.path.basename(file)
        if '.so.' in full_name:
            return full_name.split('.so.')[0]
        pattern = r"(.*)-(\d+\.\d+)"
        all_match = re.search(pattern, os.path.basename(file))
        if all_match:
            return all_match.group(1)

        return full_name

    @staticmethod
    def get_elfname(file):
        cmd = f'objdump -p {file}'
        ret, out, err = shell_cmd(cmd.split())
        if not ret and out:
            match = re.search(r'SONAME\s(.+)\s', out)
            if match:
                return match.groups()[0].strip()
        return os.path.basename(file)

    @staticmethod
    def _upsert_query_result(elfname, query_results, symbol):
        effect_rpm_so, effect_rpm = [], []
        for single_record in query_results:
            effect = {
                'elf_name': elfname,
                'symbol': symbol,
                'effect_elf': single_record.so_name,
                'effect_rpm': single_record.rpm_name
            }
            effect_rpm_so.append(effect)
            effect_rpm.append(single_record.rpm_name)

        return effect_rpm_so, effect_rpm

    def collect_effect_rpm_by_symbol(self, symbol_result, file):
        so_file_result, effect_rpms = {}, []
        elf_name = self.get_elfname(file)
        for form, symbols in symbol_result.items():
            if 'Added' in form or not symbols:
                continue
            for symbol in symbols:
                filters = {'u_symbol_table': symbol, 'association_so_name': f'"{elf_name}"'}
                query_results = self.rpm_controller.query_symbol_contains_so(filters)
                logger.debug("Query %s->%s effected record.", elf_name, symbol)
                if query_results:
                    effect_details, ef_rpm = self._upsert_query_result(elf_name, query_results, symbol)
                    effect_rpms.extend(ef_rpm)
                    so_file_result.setdefault(form, []).extend(effect_details)

        return so_file_result, list(set(effect_rpms))

    @staticmethod
    def collect_in_symbols(elf_file):
        removed_symbols = {}
        defined_symbols = []
        cmd = "nm -D {} --defined-only ".format(elf_file)
        ret, out, err = shell_cmd(cmd.split())
        if not ret and out:
            for symbol in out.split('\n'):
                if not symbol:
                    continue
                defined_symbols.append(symbol.split()[-1])
        removed_symbols.setdefault(REMOVED_DEFINED, set(defined_symbols))

        return removed_symbols

    @staticmethod
    def _save_result(file_path, content):
        with open(file_path, "w") as f:
            f.write(content)

    @staticmethod
    def _count_abi_change_result(symbol_result):
        count_result = {}
        for form, result in symbol_result.items():
            if result:
                count_result.setdefault(form, len(result))
        return count_result

    def abidiff_common_pairs(self, pair, debug_paths):
        # 设定returncode初始值，不含debuginfo调试信息abidiff比较超时则该特定值不变
        returncode = 4
        out, err = "", ""
        try:
            if all(debug_paths):
                cmd = f"abidiff {pair[0]} {pair[1]} --d1 {debug_paths[0]} --d2 {debug_paths[1]}"
            else:
                cmd = f"abidiff {pair[0]} {pair[1]}"
            logger.debug(cmd)
            returncode, out, err = shell_cmd(cmd.split(), timeout=1800)
        except TimeoutExpired as error:
            logger.error(f"TimeoutExpired Error: {error}")
            if all(debug_paths):
                returncode, out, err = self.abidiff_common_pairs(pair, ['', ''])

        return returncode, out, err

    def _compare_result(self, dump_a, dump_b, single_result=CMP_RESULT_SAME):
        count_result = {'more_count': 0, 'less_count': 0, 'diff_count': 0}
        kind = dump_a['kind']
        rpm_a, rpm_b = dump_a['rpm'], dump_b['rpm']
        result = CompareResultComposite(CMP_TYPE_RPM, single_result, rpm_a, rpm_b, dump_a['category'])
        debuginfo_rpm_path_a, debuginfo_rpm_path_b = dump_a['debuginfo_extract_path'], dump_b['debuginfo_extract_path']

        dump_a_files, dump_b_files = dump_a[self.data], dump_b[self.data]
        flag_v_r_d = self.extract_version_flag(dump_a['rpm'], dump_b['rpm'])
        common_pairs, remove_files, _ = self.format_fullpath_files(dump_a_files, dump_b_files, flag_v_r_d)

        if not common_pairs and not remove_files:
            return result
        debuginfo_rpm_path_a = os.path.join(debuginfo_rpm_path_a, 'usr/lib/debug') if debuginfo_rpm_path_a else ''
        debuginfo_rpm_path_b = os.path.join(debuginfo_rpm_path_b, 'usr/lib/debug') if debuginfo_rpm_path_b else ''
        for pair in common_pairs:
            base_a, base_b = os.path.basename(pair[0]), os.path.basename(pair[1])
            file_a, file_b = pair[0].split(self.split_flag)[-1], pair[1].split(self.split_flag)[-1]
            ret, out, err = self.abidiff_common_pairs(pair, [debuginfo_rpm_path_a, debuginfo_rpm_path_b])
            if err:
                logger.warning(f"RPM {RPMProxy.rpm_name(rpm_b)} file {file_b.split(self.split_flag)[-1]} err: {err}")
            if not out:
                if ret == 4:
                    break
                else:
                    logger.debug("check abi same")
                    data = CompareResultComponent(CMP_TYPE_RPM_SYMBOL, CMP_RESULT_SAME, file_a, file_b)
                    result.add_component(data)
            else:
                detail_result = {}
                verbose_cmp_path = f'{rpm_a}__cmp__{rpm_b}'
                base_dir = os.path.join(self._work_dir, kind, verbose_cmp_path)
                if not os.path.exists(base_dir):
                    os.makedirs(base_dir)
                file_path = os.path.join(base_dir, f'{base_a}__cmp__{base_b}.md')
                self._save_result(file_path, out)

                symbol_result = self._extract_changed_abi(out)
                if symbol_result:
                    logger.info("Extract %s changed abi: %s", base_a, symbol_result)
                all_effect_info, effect_rpm = self.collect_effect_rpm_by_symbol(symbol_result, pair[0])
                if effect_rpm:
                    logger.debug("%s: %s effect rpms:%s", rpm_b, base_b, effect_rpm)
                    detail_result.setdefault('effect_rpm', effect_rpm)
                if all_effect_info:
                    detail_result.setdefault('effect_result', all_effect_info)
                abi_count_result = self._count_abi_change_result(symbol_result)
                if abi_count_result:
                    detail_result.setdefault('count_result', abi_count_result)
                data = CompareResultComponent(CMP_TYPE_RPM_SYMBOL, CMP_RESULT_DIFF, file_a, file_b, detail_result)
                count_result["diff_count"] += 1
                result.set_cmp_result(CMP_RESULT_DIFF)
                result.add_component(data)
        if remove_files:
            all_effect_rpm, removed_file_name = [], []
            for removed_file in remove_files:
                detail_result = {}
                in_symbol_result = self.collect_in_symbols(removed_file)
                _, effect_rpm = self.collect_effect_rpm_by_symbol(in_symbol_result, removed_file)
                detail_result.setdefault('effect_rpm', effect_rpm)
                data = CompareResultComponent(CMP_TYPE_RPM_SYMBOL, CMP_RESULT_LESS,
                                              removed_file.split(self.split_flag)[-1], '', detail_result)
                count_result["less_count"] += 1
                removed_file_name.append(os.path.basename(removed_file))
                all_effect_rpm.extend(effect_rpm)
                result.set_cmp_result(CMP_RESULT_DIFF)
                result.add_component(data)
            logger.debug("%s remove files contains: %s, and effect rpms: %s", rpm_b, removed_file_name, all_effect_rpm)
        result.add_count_info(count_result)

        return result

    def compare(self):
        compare_list = []
        if not self.rpm_controller:
            logger.warning('RPM Symbol database connection failed!')
            return compare_list
        for dump_a in self.dump_a:
            for dump_b in self.dump_b:
                if RPMProxy.rpm_name(dump_a['rpm']) == RPMProxy.rpm_name(dump_b['rpm']):
                    result = self._compare_result(dump_a, dump_b)
                    logger.debug(result)
                    compare_list.append(result)
        return compare_list

    def run(self):
        result = self.compare()
        return result
