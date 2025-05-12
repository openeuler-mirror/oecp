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
from abc import ABC, abstractmethod

from oecp.proxy.rpm_proxy import RPMProxy
from oecp.utils.shell import shell_cmd
from oecp.result.constants import STAND_DISTS, BASE_SIDE, OSV_SIDE, CMP_TYPE_KCONFIG, CMP_RESULT_MORE, PAT_SO, \
    CMP_RESULT_LESS, CMP_RESULT_SAME, CMP_RESULT_DIFF, CMP_RESULT_CHANGE, CMP_RESULT_LINK_CHANGE, CMP_TYPE_RPM_ABI, \
    PAT_DIR_VERSION, PAT_VER_CHANGED, CMP_TYPE_RPM_LIB, PAT_JAR, UPSTREAM_DIST, CHANGE_FORMATS, CMP_TYPE_KO

# 两者category指定的级别不同或者未指定
CPM_CATEGORY_DIFF = 4

logger = logging.getLogger('oecp')


class CompareExecutor(ABC):

    def __init__(self, dump_a, dump_b, config):
        self.dump_a = dump_a
        self.dump_b = dump_b
        self.config = config
        self.data = 'data'
        self.split_flag = '__rpm__'
        self.link = '_[link]_'
        self.base_dist = STAND_DISTS.get(BASE_SIDE)
        self.osv_dist = STAND_DISTS.get(OSV_SIDE)
        self.re_version = re.compile("|".join(PAT_VER_CHANGED))

    @staticmethod
    def get_soname(library_file):
        cmd = f'objdump -p {library_file}'
        ret, out, err = shell_cmd(cmd.split())
        if not ret and out:
            match = re.search(r'SONAME\s(.+)\s', out)
            if match:
                so_name = match.groups()[0].strip()
                return so_name

        return library_file

    @staticmethod
    def clear_file_change_ext(file_path):
        """
        去掉压缩文件后缀，能够识别文件与它的压缩文件名
        @param file_path:
        @return:
        """
        _, file_ext = os.path.splitext(file_path)
        if file_ext in CHANGE_FORMATS:
            return file_path.rstrip(file_ext)

        return file_path

    def get_version_change_files(self, base_file, other_file, flag_ver=None):
        base_floders = base_file.split('/')
        other_floders = other_file.split('/')
        compare_result = CMP_RESULT_CHANGE
        if len(base_floders) == len(other_floders):
            for index in range(1, len(base_floders) - 1):
                floder_base, floder_other = base_floders[index], other_floders[index]
                simp_floder_base = re.sub(self.re_version, '', floder_base)
                simp_floder_other = re.sub(self.re_version, '', floder_other)
                if floder_base == floder_other:
                    continue
                elif floder_base.replace(self.base_dist, '') == floder_other.replace(self.osv_dist, ''):
                    continue
                elif flag_ver and floder_base.replace(flag_ver[0], '') == floder_other.replace(flag_ver[1], ''):
                    continue
                elif simp_floder_base == simp_floder_other:
                    continue
                elif floder_base in UPSTREAM_DIST and floder_other in UPSTREAM_DIST:
                    continue
                else:
                    compare_result = CMP_RESULT_DIFF
                    break
            return compare_result
        else:
            return CMP_RESULT_DIFF

    def get_library_pairs(self, base_file, other_file):
        base_soname = self.get_soname(base_file)
        other_soname = self.get_soname(other_file)
        if base_soname == other_soname:
            return True

        return False

    def split_files_mapping(self, dump_files, model=''):
        map_files = {}
        for focus_file in dump_files:
            # 剔除rlib库
            if model == CMP_TYPE_RPM_ABI and focus_file.endswith('.rlib'):
                continue
            if model == CMP_TYPE_KO:
                map_files.setdefault(os.path.basename(focus_file).split('.')[0], focus_file)
            else:
                map_files.setdefault(focus_file.split(self.split_flag)[-1], focus_file)

        return map_files

    def match_library_pairs(self, base_datas, other_datas, flag_vrd, model):
        map_base_libs = self.split_files_mapping(base_datas, model)
        map_other_libs = self.split_files_mapping(other_datas, model)
        base_files, other_files = set(map_base_libs.keys()), set(map_other_libs.keys())
        common_dump = base_files & other_files
        only_base_dump = base_files - other_files
        only_other_dump = other_files - base_files
        dump_lib_changed, dump_exist = [], []
        less_dump, more_dump = only_base_dump, only_other_dump
        lib_pattern = re.compile(PAT_SO)
        for other_lib in sorted(only_other_dump):
            for base_lib in sorted(only_base_dump):
                if base_lib in dump_exist:
                    continue
                elif len(list(filter(lambda x: x.endswith('.jar'), [base_lib, other_lib]))) == 1:
                    continue

                base_libname, other_libname = os.path.basename(base_lib), os.path.basename(other_lib)
                if base_lib.endswith('.jar'):
                    lib_pattern = re.compile(PAT_JAR)
                cut_base_name = re.sub(lib_pattern, '', base_libname)
                cut_other_name = re.sub(lib_pattern, '', other_libname)
                if cut_base_name.lstrip('_') != cut_other_name.lstrip('_'):
                    continue
                path_result = self.get_version_change_files(base_lib, other_lib, flag_vrd)
                full_base_lib = map_base_libs.get(base_lib)
                full_other_lib = map_other_libs.get(other_lib)
                soname_result = self.get_library_pairs(full_base_lib, full_other_lib)
                if path_result == CMP_RESULT_CHANGE or soname_result:
                    dump_exist.append(base_lib)
                    less_dump.discard(base_lib)
                    more_dump.discard(other_lib)
                    if model == CMP_TYPE_RPM_LIB:
                        dump_lib_changed.append([base_lib, other_lib])
                    else:
                        dump_lib_changed.append([full_base_lib, full_other_lib])
                    break
        if model == CMP_TYPE_RPM_LIB:
            return [
                [[x, x, CMP_RESULT_SAME] for x in common_dump],
                [[x[0], x[1], CMP_RESULT_CHANGE] for x in dump_lib_changed],
                [[x, '', CMP_RESULT_LESS] for x in less_dump],
                [['', x, CMP_RESULT_MORE] for x in more_dump]
            ]

        common_dump = [[map_base_libs.get(x), map_other_libs.get(x)] for x in common_dump]
        common_dump.extend(dump_lib_changed)
        return common_dump

    def format_changed_files(self, base_dumps, other_dumps, flag_vrd):
        """
        识别文件路径、文件名中存在以rpm包（version+release+dist/dist标识/x.x.x版本号）命名的相同文件对
        @param base_dumps: 缺失文件
        @param other_dumps: 新增文件
        @param flag_vrd: version+release+dist标识
        """
        only_dump_base = base_dumps - other_dumps
        only_dump_other = other_dumps - base_dumps
        change_dump = []
        datas_base = self.mapping_files(only_dump_base, flag_vrd[0], self.base_dist)
        datas_other = self.mapping_files(only_dump_other, flag_vrd[1], self.osv_dist)
        for simple_file in datas_other.keys():
            if datas_base.get(simple_file):
                base_file = datas_base.get(simple_file)
                other_file = datas_other.get(simple_file)
                change_dump.append([base_file, other_file])
                only_dump_base.discard(base_file)
                only_dump_other.discard(other_file)

        sort_other_files, sort_base_files = sorted(only_dump_other), sorted(only_dump_base)
        for other_file in sort_other_files:
            for base_file in sort_base_files:
                if base_file not in only_dump_base:
                    continue
                get_result = CMP_RESULT_DIFF
                split_base_file = base_file.split(self.link)[0]
                split_other_file = other_file.split(self.link)[0]
                base_so_truncate_ver = re.sub(PAT_SO, '', os.path.basename(split_base_file))
                other_so_truncate_ver = re.sub(PAT_SO, '', os.path.basename(split_other_file))
                if other_so_truncate_ver == base_so_truncate_ver:
                    get_result = self.get_version_change_files(split_base_file, split_other_file)
                else:
                    basename = re.sub(self.re_version, '', os.path.basename(split_base_file))
                    othername = re.sub(self.re_version, '', os.path.basename(split_other_file))
                    if self.get_same_filename_pair(basename, othername):
                        get_result = self.get_version_change_files(split_base_file, split_other_file)
                if get_result == CMP_RESULT_DIFF:
                    continue
                change_dump.append([base_file, other_file])
                only_dump_base.discard(base_file)
                only_dump_other.discard(other_file)
                break

        return change_dump, only_dump_base, only_dump_other

    def format_dump(self, base_datas, other_datas, flag_vrd):
        base_files = set([data.split(self.split_flag)[-1] for data in base_datas])
        other_files = set([data.split(self.split_flag)[-1] for data in other_datas])
        common_dump = base_files & other_files
        change_dump, only_base_dump, only_other_dump = self.format_changed_files(base_files, other_files, flag_vrd)

        return [
            [[x, x, CMP_RESULT_SAME] for x in common_dump],
            [self.judge_changed_type(x, flag_vrd) for x in change_dump],
            [[x, '', CMP_RESULT_LESS] for x in only_base_dump],
            [['', x, CMP_RESULT_MORE] for x in only_other_dump]
        ]

    def format_fullpath_files(self, base_datas, other_datas, flag_vrd):
        map_base_files = self.split_files_mapping(base_datas)
        map_other_files = self.split_files_mapping(other_datas)
        base_files, other_files = set(map_base_files.keys()), set(map_other_files.keys())
        common_dump = base_files & other_files
        change_dump, only_base_dump, only_other_dump = self.format_changed_files(base_files, other_files, flag_vrd)
        common_pairs = [[map_base_files.get(y), map_other_files.get(y)] for y in common_dump]
        common_pairs.extend([[map_base_files.get(y[0]), map_other_files.get(y[1])] for y in change_dump])

        return common_pairs, only_base_dump, only_other_dump

    def get_same_filename_pair(self, base_file, other_file):
        """
        判断是否为相同文件
        @param base_file:
        @param other_file:
        @return:
        """
        base_clear_format = self.clear_file_change_ext(base_file)
        other_clear_format = self.clear_file_change_ext(other_file)
        if base_clear_format.lower() == other_clear_format.lower():
            return True
        elif base_clear_format.replace(self.base_dist, '') == other_clear_format.replace(self.osv_dist, ''):
            return True
        else:
            return False

    def mapping_files(self, files, flag_vrd, dist):

        map_result = {}
        for file in sorted(files):
            dir_pattern = re.compile("|".join(PAT_DIR_VERSION))
            truncate_vrd_dist = file.replace(flag_vrd, '').replace(dist, '')
            target_file_path = truncate_vrd_dist.split(self.link)[0]
            truncate_dir_version = re.sub(dir_pattern, '', os.path.dirname(target_file_path))
            truncate_newfile = os.path.join(truncate_dir_version, os.path.basename(target_file_path))
            clear_format_filename = self.clear_file_change_ext(truncate_newfile)
            map_result.setdefault(clear_format_filename, file)

        return map_result

    def judge_changed_type(self, pair, flag_vrd):
        base_file, other_file = pair[0], pair[1]
        link_result = list(filter(lambda x: self.link in x, [base_file, other_file]))
        if not link_result:
            base_name, other_name = os.path.basename(base_file), os.path.basename(other_file)
            if base_name == other_name:
                changed_result = [base_file, other_file, CMP_RESULT_CHANGE]
            elif base_name.replace(self.base_dist, '') == other_name.replace(self.osv_dist, ''):
                changed_result = [base_file, other_file, CMP_RESULT_CHANGE]
            else:
                changed_result = [base_file, other_file, CMP_RESULT_CHANGE]
        elif len(link_result) == 1:
            changed_result = [base_file, other_file, CMP_RESULT_LINK_CHANGE]
        else:
            base_linkfile, base_target_file = base_file.split(self.link)
            other_linkfile, other_target_file = other_file.split(self.link)
            link_target_a = re.sub(self.re_version, '', base_target_file.replace(flag_vrd[0], ''))
            link_target_b = re.sub(self.re_version, '', other_target_file.replace(flag_vrd[1], ''))
            if base_target_file == other_target_file:
                changed_result = [base_file, other_file, CMP_RESULT_CHANGE]
            elif link_target_a == link_target_b:
                changed_result = [base_file, other_file, CMP_RESULT_CHANGE]
            else:
                changed_result = [base_file, other_file, CMP_RESULT_LINK_CHANGE]

        return changed_result

    def format_dump_file(self, data_a, data_b):
        common_dump = data_a & data_b
        only_dump_a = data_a - data_b
        only_dump_b = data_b - data_a
        common_dump_result = [[x, x, CMP_RESULT_SAME] for x in common_dump]
        common_dump_a, common_dump_b = [], []
        for side_a in only_dump_a:
            for side_b in only_dump_b:
                if side_a.replace(self.base_dist, "") == side_b.replace(self.osv_dist, ""):
                    common_dump_result.append([side_a, side_b, CMP_RESULT_SAME])
                    common_dump_a.append(side_a)
                    common_dump_b.append(side_b)
                    break
        only_dump_a = only_dump_a - set(common_dump_a)
        only_dump_b = only_dump_b - set(common_dump_b)
        all_dump = [
            common_dump_result,
            [[x, '', CMP_RESULT_LESS] for x in only_dump_a],
            [['', x, CMP_RESULT_MORE] for x in only_dump_b]
        ]

        return all_dump

    @staticmethod
    def check_diff_info(out):
        lack_conf_flag = False
        for compare_line in out.split('\n')[3:]:
            if not compare_line:
                continue
            lack_conf = re.match('-', compare_line)
            openeuler_conf = re.search('openEuler', compare_line)
            if lack_conf and not openeuler_conf:
                lack_conf_flag = True
                break

        return lack_conf_flag

    @staticmethod
    def component_new_provide(datas):
        all_pvds = [' '.join([pvd['name'], pvd['symbol'], pvd['version'].split('-')[0]]) for pvd in datas]

        return set(all_pvds)

    @staticmethod
    def pretty_provide_datas(datas, flag_vrd):
        # provides 版本固定时，不比较版本号
        pretty_result = {}
        pat_so = re.compile(r"(-?\d*([-_.]\d+){0,3}(\.cpython-(.*)-linux-gnu)?\.so([-_.][\dA-Za-z]+){0,4})"
                            r"|-[a-z0-9]{16}.so|python\d(\.\d+)?|([-_.]\d+){0,3}")
        for pvd in datas:
            pvd_name = pvd['name']
            pvd_symbol = pvd['symbol']
            new_component = ' '.join([pvd_name, pvd_symbol, pvd['version'].split('-')[0]])
            if flag_vrd in pvd_name:
                # "application(java-1.8.0-openjdk-1.8.0.272.b10-7.oe1.aarch64-policytool.desktop)"
                pvd_name = pvd_name.replace(flag_vrd, '')

            if re.search(pat_so, pvd_name):
                pvd_name = re.sub(pat_so, '', pvd_name)
            # provides版本不固定
            elif pvd_symbol in [">=", "<="]:
                pvd_name = ''.join(new_component.split(flag_vrd))
            pretty_result.setdefault(pvd_name, []).append(new_component)

        return pretty_result

    def format_ko_files(self, base_datas, other_datas):
        common_pairs, only_other = [], []
        common_ko_names = []
        for other_ko_name in other_datas:
            if base_datas.get(other_ko_name):
                common_pairs.append([base_datas.get(other_ko_name), other_datas.get(other_ko_name)])
                common_ko_names.append(other_ko_name)
            else:
                only_other.append(other_datas.get(other_ko_name).split(self.split_flag)[-1])

        only_base_ko = set(base_datas.keys()) - set(common_ko_names)
        only_base = [base_datas.get(ko_name).split(self.split_flag)[-1] for ko_name in only_base_ko]

        return common_pairs, only_base, only_other

    @staticmethod
    def format_ko_info(base_ko_info, other_ko_info):
        same_info = []
        diff_info = []
        less_info = []
        for item, base_info in base_ko_info.items():
            other_info = other_ko_info.get(item, None)
            if re.match('^alias', item):
                base_info = '\n'.join(sorted(base_info))
                other_info = '\n'.join(sorted(other_info))
            if base_info == other_info:
                same_info.append([' '.join([item, base_info]), ' '.join([item, base_info]), CMP_RESULT_SAME])
            elif re.match('^license', item) and re.sub(r"\sv\d", '', base_info) == re.sub(r"\sv\d", '', other_info):
                same_info.append([' '.join([item, base_info]), ' '.join([item, other_info]), CMP_RESULT_SAME])
            elif re.match('^vermagic', item):
                match_ver_base = re.match(r"(.+)-(\S+).*", base_info.split()[0])
                match_ver_other = re.match(r"(.+)-(\S+).*", other_info.split()[0])
                if base_info.replace(match_ver_base.group(2), '') == other_info.replace(match_ver_other.group(2), ''):
                    same_info.append([' '.join([item, base_info]), ' '.join([item, other_info]), CMP_RESULT_SAME])
                else:
                    diff_info.append([' '.join([item, base_info]), ' '.join([item, other_info]), CMP_RESULT_DIFF])
            else:
                if other_info is None:
                    less_info.append([' '.join([item, base_info]), '', CMP_RESULT_LESS])
                else:
                    diff_info.append([' '.join([item, base_info]), ' '.join([item, other_info]), CMP_RESULT_DIFF])
        more_info = set(other_ko_info.keys()) - set(base_ko_info.keys())

        all_dump = [
            same_info,
            diff_info,
            less_info,
            [['', ' '.join([more, other_ko_info.get(more)]), CMP_RESULT_MORE] for more in more_info]
        ]

        return all_dump

    def format_dump_provides(self, base_datas, other_datas, flag_vrd):
        common_files, common_file_a, common_file_b = [], [], []
        prov_base = self.pretty_provide_datas(base_datas, flag_vrd[0])
        prov_other = self.pretty_provide_datas(other_datas, flag_vrd[1])
        for side_a in prov_base.keys():
            if prov_other.get(side_a):
                pvds_a = sorted(prov_base.get(side_a))
                pvds_b = sorted(prov_other.get(side_a))
                common_files.append([','.join(pvds_a), ','.join(pvds_b), CMP_RESULT_SAME])
                common_file_a.extend(pvds_a)
                common_file_b.extend(pvds_b)

        all_components_a = self.component_new_provide(base_datas)
        all_components_b = self.component_new_provide(other_datas)
        only_file_a = all_components_a - set(common_file_a)
        only_file_b = all_components_b - set(common_file_b)

        all_dump = [
            common_files,
            [[x, '', CMP_RESULT_LESS] for x in only_file_a],
            [['', x, CMP_RESULT_MORE] for x in only_file_b]
        ]

        return all_dump

    @staticmethod
    def format_dump_kv(data_a, data_b, kind):
        list_a = list(data_a)
        list_b = list(data_b)
        h_a = {}
        h_b = {}
        same = []
        diff = []
        less = []
        all_dump = []

        for a in list_a:
            t = a.split(" = ")
            h_a[t[0]] = t[0] + " " + t[1]

        for b in list_b:
            t = b.split(" = ")
            h_b[t[0]] = t[0] + " " + t[1]

        for k, va in h_a.items():
            vb = h_b.get(k, None)
            if vb is None:
                less.append([va, '', CMP_RESULT_LESS])
            elif va == vb:
                same.append([va, vb, CMP_RESULT_SAME])
            elif va.split()[-1] in ('m', 'y') and vb.split()[-1] in ('m', 'y'):
                same.append([va, vb, CMP_RESULT_SAME])
            else:
                diff.append([va, vb, CMP_RESULT_DIFF])

        all_dump.append(same)
        all_dump.append(diff)
        all_dump.append(less)

        if kind == CMP_TYPE_KCONFIG:
            more = []
            for k, vb, in h_b.items():
                va = h_a.get(k, None)
                if va is None:
                    more.append(['', vb, CMP_RESULT_MORE])

            if more:
                all_dump.append(more)

        return all_dump

    @staticmethod
    def extract_version_flag(rpm_a, rpm_b):
        """
        获取俩比较rpm包的version、release标识
        @param rpm_a: rpm包名
        @param rpm_b: rpm包名
        @return:
        """
        n_a, _, _, _, a_a = RPMProxy.rpm_n_v_r_d_a(rpm_a)
        n_b, _, _, _, a_b = RPMProxy.rpm_n_v_r_d_a(rpm_b)

        v_r_d_a = rpm_a.split(a_a)[0].split(n_a)[-1]
        v_r_d_b = rpm_b.split(a_b)[0].split(n_b)[-1]
        flag_v_r_d = [v_r_d_a.strip('-.'), v_r_d_b.strip('-.')]
        if not flag_v_r_d:
            logging.warning(f"{rpm_a} and {rpm_b} extract version_release_dist flag failed!")

        return flag_v_r_d

    @staticmethod
    def format_service_detail(data_base, data_other, file_result=CMP_RESULT_SAME):
        same = []
        diff = []
        data_conf_base, data_conf_other = list(data_base.keys()), list(data_other.keys())
        same_conf = set(data_conf_base) & set(data_conf_other)
        lost_conf = set(data_conf_base) - set(data_conf_other)
        more_conf = set(data_conf_other) - set(data_conf_base)
        for conf in same_conf:
            detail_base = data_base.get(conf)
            detail_other = data_other.get(conf)
            if detail_base == detail_other:
                same.append([' '.join([conf, "=", detail_base]), ' '.join([conf, "=", detail_other]), CMP_RESULT_SAME])
            else:
                diff.append(
                    [' '.join([conf, "=", detail_base]), ' '.join([conf, "=", detail_other]), CMP_RESULT_DIFF])
        if diff or lost_conf:
            file_result = CMP_RESULT_DIFF
        all_dump = [
            same,
            diff,
            [[' '.join([conf, "=", data_base.get(conf)]), '', CMP_RESULT_LESS] for conf in lost_conf],
            [['', ' '.join([conf, "=", data_other.get(conf)]), CMP_RESULT_MORE] for conf in more_conf]
        ]

        return file_result, all_dump

    @staticmethod
    def _set_so_mapping(library_files):
        if not library_files:
            return {}

        so_mapping = {}
        for library_file in library_files:
            cmd = f'objdump -p {library_file}'
            ret, out, err = shell_cmd(cmd.split())
            if not ret and out:
                match = re.search(r'SONAME\s(.+)\s', out)
                if match:
                    so_name = match.groups()[0].strip()
                    so_mapping.setdefault(so_name, library_file)
        return so_mapping

    @abstractmethod
    def run(self):
        pass
