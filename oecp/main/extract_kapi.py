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
import concurrent
import os
import re
import logging
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool, cpu_count
import yaml

from oecp.utils.shell import shell_cmd
from oecp.result.constants import CMP_TYPE_RPM_KERNEL, MACRO_DEFINE, MACRO_DECLARE, EXTERN

logger = logging.getLogger('oecp')


class EXTRACTKAPI(object):

    def __init__(self):
        self.whitelist = []
        self.src_dirs = [
            "include",
            "arch/arm64/include",
            "arch/x86/include",
            "drivers",
            "kernel/module"
        ]
        self.conf_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "conf/kapi_whitelist")
        self.load_whitelist()

    @staticmethod
    def _is_new_line(line):
        return re.match(r"^\w+", line)

    @staticmethod
    def load_conf(conf_path):
        with open(conf_path, 'r', encoding='utf-8') as conf:
            result = yaml.safe_load(conf)

        return result

    @staticmethod
    def get_dir_path(src_obj, base_dir):
        if isinstance(src_obj, str):
            return os.path.join(src_obj, CMP_TYPE_RPM_KERNEL, base_dir)
        src_path = os.path.join(src_obj.name, CMP_TYPE_RPM_KERNEL, base_dir)

        return src_path

    @staticmethod
    def get_acpi_whitelist_function(component_args):
        models, symbol, _, contents, func_return = component_args
        match_flag = False
        fun_pattern = r"( )+(\*)?(%s)\([\w\s\*,\n]+?\)\)" % symbol
        if symbol.startswith("acpi_"):
            model_match = re.search(fun_pattern, contents)
            if model_match:
                all_lines = model_match.group().split('\n')
                all_lines.insert(0, func_return.split('(')[-1])
                model = " ".join(list(map(lambda x: x.strip(), all_lines)))
                model = re.sub(r'\)$', ';', model)
                models.append(model)
                match_flag = True
            else:
                model_match = re.search(r"ACPI_GLOBAL\([\w, ]*%s\);" % symbol, contents)
                if model_match:
                    models.append(model_match.group())
                    match_flag = True

        return match_flag

    def get_declare_macro(self, component_args):
        models, symbol, model, _, fun_return = component_args
        match_flag = False
        if re.match(r'[\t| ]+', model):
            model = ''.join([fun_return, model.lstrip()])
        define_macro = re.match(r"%s_[A-Z_]+\([\w\*, ]*%s\);" % (MACRO_DECLARE, symbol), model)
        if define_macro:
            models.append(define_macro.group().replace(MACRO_DECLARE, MACRO_DEFINE))
            match_flag = True
        define_macro = re.match(r"([A-Z_]+)%s\((.*)\);" % MACRO_DECLARE, model)
        if define_macro:
            if symbol in define_macro.group(2):
                models.append(model)
                match_flag = True

        return match_flag

    def load_attrs_macros(self):
        conf_attrs = os.path.join(self.conf_path, "attrs_and_macros.yaml")
        attrs_and_macros = self.load_conf(conf_attrs)

        return attrs_and_macros

    def load_whitelist(self):
        whitelist_path = os.path.join(self.conf_path, "kapi_whitelist.yaml")
        self.whitelist = self.load_conf(whitelist_path)

    def cut_macro_or_attr(self, match):
        attrs = self.load_attrs_macros()
        make_attrs = attrs.get("make_attrs")
        after_attrs = attrs.get("after_attrs")
        for attr in make_attrs:
            attr_pattern = re.compile(attr)
            if re.search(attr_pattern, match):
                match = re.sub(attr_pattern, "", match)

        for attr in after_attrs:
            match = re.sub(attr, "", match)

        return match

    def cut_before_attrs(self, fun_return):
        attrs = self.load_attrs_macros()
        before_attrs = attrs.get("before_attrs")
        for macro in before_attrs:
            fun_return = re.sub(r"%s( )?" % macro, "", fun_return)

        return fun_return

    def prase_fun_return(self, symbol, model, contents):
        fun_return = model.lstrip().split(symbol)[0]
        filter_model = False
        if not fun_return or fun_return == "*":
            escape_model = re.escape(model)
            last_pat = r"\n(.*)\n%s" % escape_model
            last_matchs = re.search(last_pat, contents)
            if last_matchs:
                fun_return = last_matchs.group(1)
                if fun_return.startswith("#"):
                    filter_model = True
        fun_return = self.cut_before_attrs(fun_return)
        if not re.match(r".* \*{1,2}$", fun_return):
            if fun_return.endswith(" * "):
                fun_return = fun_return.strip()
            else:
                fun_return = fun_return.strip() + " "
        fun_return = re.sub(r"^%s " % EXTERN, '', fun_return)
        for filter_symbol in [" inline ", " = ", " &= ", "do ", "{ "]:
            if filter_symbol in fun_return:
                filter_model = True

        return fun_return, filter_model

    def get_common_function(self, component_args):
        models, symbol, model, contents, fun_return = component_args
        match_flag = False
        fun_pattern = r"[\s|\*{1,2}](%s)( )*\([\w\s\*,\.\[\]\(\)]+\)([ \w]+)?;" % symbol
        model_matchs = re.finditer(fun_pattern, contents)
        for match in model_matchs:
            all_lines = match.group().split('\n')
            if all_lines[0] == "":
                del all_lines[0]
            if all_lines[0] not in model:
                continue

            if len(all_lines) > 1 and list(filter(self._is_new_line, all_lines[1:])):
                continue
            all_lines = [re.sub(r"[\t| ]+", " ", line) for line in all_lines]
            component_model = fun_return + " ".join(list(map(lambda x: x.strip(), all_lines))).lstrip("*")
            full_model = self.cut_macro_or_attr(component_model)
            check_match = re.match(r"(.*?)\([\s\S]*\);$", full_model)
            if check_match:
                check_symbol = check_match.group(1).split()[-1].lstrip("*")
                if check_symbol != symbol:
                    continue

            models.append(full_model)
            match_flag = True

        return match_flag

    def get_struct_function(self, component_args):
        models, symbol, model, contents, fun_return = component_args
        match_flag = False
        no_parm_pat = r"%s(\[[\w\+ \(\)]+\]){0,2};" % symbol
        no_parm_matchs = re.finditer(no_parm_pat, contents)
        for match in no_parm_matchs:
            if match.group() not in model:
                continue
            component_model = self.cut_macro_or_attr(fun_return + match.group())
            if re.match(r"\} %s;" % symbol, component_model):
                func_match = re.search(r"%s ([\w ]+)\{[\s\S]+%s" % (EXTERN, model), contents)
                if func_match:
                    component_model = func_match.group(1) + component_model.replace("} ", '')
            models.append(component_model)
            match_flag = True

        return match_flag

    def get_extern_function(self, component_args):
        models, symbol, model, _, _ = component_args
        match = re.match(r"^%s (.*;$)" % EXTERN, model)
        symbols = []
        match_flag = False
        if match:
            cut_model = self.cut_macro_or_attr(match.group(1))
            cut_model = self.cut_before_attrs(cut_model)
            cut_model = re.sub(r"/\*(.*)\*/ ", "", cut_model)
            func_match = re.search(r"(\w+)\(([\w\*, ]*)\);", cut_model)
            if not func_match:
                symbols.append(cut_model)
            else:
                symbol_match = func_match.group(1)
                if symbol_match == symbol:
                    symbols.append(cut_model)
                elif re.match(r"%s[A-Z_]+" % MACRO_DECLARE, symbol_match) and symbol in func_match.group(2):
                    symbols.append(cut_model)
        if symbols:
            models.extend(symbols)
            match_flag = True

        return match_flag

    def get_kapi_prototype(self, symbol, src_obj):
        models = []
        for base_dir in self.src_dirs:
            src_path = self.get_dir_path(src_obj, base_dir)
            if not os.path.exists(src_path):
                logger.debug("not exists %s in source kernel", src_path)
                continue
            cmd = ['grep', '-rnw', '-e', symbol, src_path, '--include=*.h']
            code, out, err = shell_cmd(cmd)
            if not code:
                all_search_info = out.split('\n')
                for single_info in all_search_info:
                    if not single_info:
                        continue
                    header_file, model = re.split(r':\d+:', single_info)
                    if re.match(r'[\t| ]+', model):
                        if symbol not in self.whitelist:
                            continue
                    elif model.startswith(('#', '* ', '/*', '"', 'return')):
                        continue

                    with open(header_file, 'r') as f:
                        contents = f.read()

                    fun_return, filter_model = self.prase_fun_return(symbol, model, contents)
                    component_args = (models, symbol, model, contents, fun_return)
                    if filter_model:
                        continue
                    elif self.get_extern_function(component_args):
                        continue
                    elif self.get_common_function(component_args):
                        continue
                    elif self.get_struct_function(component_args):
                        continue
                    elif self.get_declare_macro(component_args):
                        continue
                    elif self.get_acpi_whitelist_function(component_args):
                        continue

            elif code != 1:
                logger.error("Get symbol %s error, code %s.", symbol, code)

            if models:
                break

        model = '\n'.join(sorted(set(models)))
        if not model:
            logger.debug("Not get kapi function prototype of kabi symbol %s", symbol)

        return model

    def multiprocess_get_prototype(self, kabi_symbols, src_obj):
        """
        异步查询kapi函数原型
        @param kabi_symbols: 需要查找的kabi符号列表
        @param src_obj: 内核源码包临时目录/内核源码路径
        @return:
        """
        component_results = {}

        def callback(model, symbol):
            component_results[symbol] = model

        def wrapper_callback(symbol):
            return lambda model: callback(model, symbol)

        pool = Pool(cpu_count())
        try:
            for symbol in kabi_symbols:
                pool.apply_async(self.get_kapi_prototype, (symbol, src_obj), callback=wrapper_callback(symbol))
        except KeyboardInterrupt:
            pool.terminate()

        pool.close()
        pool.join()

        return dict(sorted(component_results.items()))

    def multithread_get_prototype(self, symbols, src_obj):
        component_results = {}
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(self.get_kapi_prototype, symbol, src_obj): symbol
                for symbol in symbols
            }
            for future in concurrent.futures.as_completed(futures):
                symbol = futures[future]
                try:
                    component_results[symbol] = future.result()
                except Exception as e:
                    logger.error("get %s kapi failed, error: %s", symbol, e)

        return dict(sorted(component_results.items()))
