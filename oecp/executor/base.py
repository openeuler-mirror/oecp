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
import os
import re
import logging
import difflib
from abc import ABC, abstractmethod
from datetime import datetime

from oecp.proxy.rpm_proxy import RPMProxy
from oecp.utils.shell import shell_cmd
from oecp.result.constants import CMP_DIFF_RESULT, CMP_TYPE_KCONFIG, BASE_SIDE, OSV_SIDE, PAT_SO, CMP_SAME_FILES, \
    CMP_TYPE_RPM_ABI, CMP_RESULT_MORE, CMP_RESULT_LESS, CMP_RESULT_SAME, CMP_RESULT_DIFF, CMP_RESULT_CHANGE, \
    PAT_DIR_VERSION, PAT_VER_CHANGED, UPSTREAM_DIST, CHANGE_DIRECTORY_VERSION, CHANGE_DIST_IN_FILENAME, STAND_DISTS, \
    CHANGE_FILE_VERSION, CHANGE_FILE_TYPE, CHANGE_LINKFILE_VERSION, CHANGE_LINK_TARGET_VERSION, CHANGE_FORMATS, \
    CHANGE_FILE_FORMAT, CHANGE_LINK_TARGET_FILE

# 两者category指定的级别不同或者未指定

CPM_CATEGORY_DIFF = 4

logger = logging.getLogger('oecp')


class CompareExecutor(ABC):

    def __init__(self, base_dump, other_dump, config):
        self.base_dump = base_dump
        self.other_dump = other_dump
        self.config = config
        self.base_dist = STAND_DISTS.get(BASE_SIDE)
        self.osv_dist = STAND_DISTS.get(OSV_SIDE)
        self.re_version = re.compile("|".join(PAT_VER_CHANGED))
        self.split_flag = '__rpm__'
        self.link = '_[link]_'

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
    def format_rmp_name(data_a, data_b):
        same_pairs, commons_a, commons_b = [], [], []
        for require_details_a in data_a:
            for require_details_b in data_b:
                if require_details_a.get('name') == require_details_b.get('name'):
                    same_pairs.append([require_details_a, require_details_b, CMP_RESULT_SAME])
                    commons_a.append(require_details_a)
                    commons_b.append(require_details_b)
        require_less = [less_require for less_require in data_a if less_require not in commons_a]
        require_more = [more_require for more_require in data_b if more_require not in commons_b]
        all_dump = [
            same_pairs,
            [[single_less, '', CMP_RESULT_LESS] for single_less in require_less],
            [['', single_more, CMP_RESULT_MORE] for single_more in require_more]
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
    def count_cmp_result(count_result, cmp_result):
        if cmp_result in CMP_SAME_FILES:
            count_result["same"] += 1
        elif cmp_result == CMP_RESULT_LESS:
            count_result["less"] += 1
        elif cmp_result == CMP_RESULT_MORE:
            count_result["more"] += 1
        elif cmp_result in CMP_DIFF_RESULT:
            count_result["diff"] += 1

    @staticmethod
    def get_equal_rate(dist_a, dist_b):
        return 1 - difflib.SequenceMatcher(None, dist_a, dist_b).quick_ratio()

    @staticmethod
    def handle_digit_type(d):
        """
        @param d: Digit types in version matching, may be a time type.
        @return:
        """
        t = re.match(r'(\d{8})', d)
        if t:
            try:
                v = datetime.strptime(t.group(1), '%Y%m%d')
            except ValueError:
                # The first five digits are used for non-time types.
                v = t.group(1)[:5]
        else:
            v = d[:5]
        return v

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
        flag = [
            v_r_d_a.strip('-.'),
            v_r_d_b.strip('-.')
        ]
        if not v_r_d_a or not v_r_d_b:
            logging.warning(f"{rpm_a} and {rpm_b} extract version_release_dist flag failed!")

        return flag

    @staticmethod
    def format_dump_file(data_a, data_b):
        dump_set_a, dump_set_b = set(data_a), set(data_b)
        common_dump = dump_set_a & dump_set_b
        only_dump_a = dump_set_a - dump_set_b
        only_dump_b = dump_set_b - dump_set_a
        common_dump_result = [[x, x, CMP_RESULT_SAME] for x in common_dump]
        common_dump_a, common_dump_b = [], []
        for side_a in only_dump_a:
            for side_b in only_dump_b:
                if side_a.split(STAND_DISTS.get(BASE_SIDE)) == side_b.split(STAND_DISTS.get(OSV_SIDE)):
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
    def pretty_provide_datas(datas, v_r_d):
        # provides 版本固定时，不比较版本号
        pretty_result = {}
        for pvd in datas:
            pvd_name = pvd['name']
            pvd_symbol = pvd['symbol']
            new_component = ' '.join([pvd_name, pvd_symbol, pvd['version'].split('-')[0]])
            pat_so = re.compile(PAT_SO)
            if re.search(pat_so, pvd_name):
                component_so_name = re.sub(pat_so, '', pvd_name)
                pretty_result.setdefault(component_so_name, []).append(new_component)
            # provides版本不固定
            elif pvd_symbol in [">=", "<="]:
                simple_name = ''.join(new_component.split(v_r_d))
                pretty_result.setdefault(simple_name, []).append(new_component)
            else:
                # "application(java-1.8.0-openjdk-1.8.0.272.b10-7.oe1.aarch64-policytool.desktop)"
                simple_name = ''.join(pvd_name.split(v_r_d))
                pretty_result.setdefault(simple_name, []).append(new_component)

        return pretty_result

    @staticmethod
    def component_new_provide(datas):
        all_pvds = [' '.join([pvd['name'], pvd['symbol'], pvd['version'].split('-')[0]]) for pvd in datas]

        return set(all_pvds)

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

    def get_version_change_files(self, base_file, other_file, flag_v=None):
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
                elif flag_v and floder_base.replace(flag_v[0], '') == floder_other.replace(flag_v[1], ''):
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

    def mapping_files(self, files, flag_vrd, dist):
        map_result = {}
        for file in sorted(files):
            # 文件目录中含软件包version-release.dist.arch标识
            dir_pattern = re.compile("|".join(PAT_DIR_VERSION))
            truncate_vrd_dist = file.replace(flag_vrd, '').replace(dist, '')
            target_file_path = truncate_vrd_dist.split(self.link)[0]
            truncate_dir_version = re.sub(dir_pattern, '', os.path.dirname(target_file_path))
            truncate_newfile = os.path.join(truncate_dir_version, os.path.basename(target_file_path))
            clear_format_filename = self.clear_file_change_ext(truncate_newfile)
            map_result.setdefault(clear_format_filename, file)

        return map_result

    def get_library_pairs(self, base_file, other_file):
        base_soname = self.get_soname(base_file)
        other_soname = self.get_soname(other_file)
        if base_soname == other_soname:
            return True

        return False

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

    def format_dump(self, base_datas, other_datas, flag_vrd):
        """
        抓取相对路径相同或版本变化的文件对
        @param base_datas: dump_base获取的文件全路径
        @param other_datas: dump_other获取的文件全路径
        @param flag_vrd: version+release+dist标识
        @return: 返回相对路径
        """
        base_files = set([data.split(self.split_flag)[-1] for data in base_datas])
        other_files = set([data.split(self.split_flag)[-1] for data in other_datas])
        common_dump = base_files & other_files
        change_dump, only_base_dump, only_other_dump = self.format_changed_files(base_files, other_files, flag_vrd)
        all_dump = [
            [[x, x, CMP_RESULT_SAME] for x in common_dump],
            [self.judge_changed_type(x, flag_vrd) for x in change_dump],
            [[x, '', CMP_RESULT_LESS] for x in only_base_dump],
            [['', x, CMP_RESULT_MORE] for x in only_other_dump]
        ]

        return all_dump

    def format_fullpath_files(self, base_datas, other_datas, flag_vrd):
        """
        抓取相对路径相同或版本变化的文件对
        @param base_datas: 基准rpm包特定类型文件
        @param other_datas: 需要对比的rpm包特定类型文件
        @param flag_vrd: version+release+dist标识
        @return: 返回绝对路径
        """
        map_base_files = self.split_files_mapping(base_datas)
        map_other_files = self.split_files_mapping(other_datas)
        base_files, other_files = set(map_base_files.keys()), set(map_other_files.keys())
        common_dump = base_files & other_files
        change_dump, only_base_dump, only_other_dump = self.format_changed_files(base_files, other_files, flag_vrd)
        common_pairs = [[map_base_files.get(y), map_other_files.get(y)] for y in common_dump]
        common_pairs.extend([[map_base_files.get(y[0]), map_other_files.get(y[1])] for y in change_dump])

        return common_pairs, only_base_dump, only_other_dump

    def map_base_files(self, base_files):
        map_result = {}
        for file in sorted(base_files):
            truncate_name = self.truncate_files(file, self.base_dist)
            map_result.setdefault(truncate_name, []).append(file)

        return map_result

    def truncate_files(self, file_path, dist):
        tru_base_file = file_path.split(self.link)[0]
        simple_name = re.sub(self.re_version, '', os.path.basename(tru_base_file))
        clear_file_format = self.clear_file_change_ext(simple_name)
        final_name = clear_file_format.replace(dist, '')

        return final_name.lower()

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

        for other_file in sorted(only_dump_other):
            simp_filename = self.truncate_files(other_file, self.osv_dist)
            map_base_files = self.map_base_files(only_dump_base)
            for base_file in map_base_files.get(simp_filename, []):
                if base_file not in only_dump_base:
                    continue
                tru_base_file = base_file.split(self.link)[0]
                tru_other_file = other_file.split(self.link)[0]
                get_result = self.get_version_change_files(tru_base_file, tru_other_file, flag_vrd)
                if get_result == CMP_RESULT_DIFF:
                    continue
                change_dump.append([base_file, other_file])
                only_dump_base.discard(base_file)
                only_dump_other.discard(other_file)
                break

        return change_dump, only_dump_base, only_dump_other

    def judge_changed_type(self, pair, flag_vrd):
        base_file, other_file = pair[0], pair[1]
        link_result = list(filter(lambda x: self.link in x, [base_file, other_file]))
        if not link_result:
            base_name, other_name = os.path.basename(base_file), os.path.basename(other_file)
            if base_name == other_name:
                changed_result = [base_file, other_file, CHANGE_DIRECTORY_VERSION]
            elif base_name.replace(self.base_dist, '') == other_name.replace(self.osv_dist, ''):
                changed_result = [base_file, other_file, CHANGE_DIST_IN_FILENAME]
            else:
                basefile_clear_ext = self.clear_file_change_ext(base_name)
                otherfile_clear_ext = self.clear_file_change_ext(other_name)
                if basefile_clear_ext == otherfile_clear_ext:
                    changed_result = [base_file, other_file, CHANGE_FILE_FORMAT]
                else:
                    changed_result = [base_file, other_file, CHANGE_FILE_VERSION]
        elif len(link_result) == 1:
            changed_result = [base_file, other_file, CHANGE_FILE_TYPE]
        else:
            base_linkfile, base_target_file = base_file.split(self.link)
            other_linkfile, other_target_file = other_file.split(self.link)
            link_target_a = re.sub(self.re_version, '', base_target_file.replace(flag_vrd[0], ''))
            link_target_b = re.sub(self.re_version, '', other_target_file.replace(flag_vrd[1], ''))
            if base_target_file == other_target_file:
                changed_result = [base_file, other_file, CHANGE_LINKFILE_VERSION]
            elif link_target_a == link_target_b:
                changed_result = [base_file, other_file, CHANGE_LINK_TARGET_VERSION]
            else:
                changed_result = [base_file, other_file, CHANGE_LINK_TARGET_FILE]

        return changed_result

    def split_files_mapping(self, dump_files, model=''):
        map_files = {}
        for focus_file in dump_files:
            # 剔除rlib库
            if model == CMP_TYPE_RPM_ABI and focus_file.endswith('.rlib'):
                continue
            map_files.setdefault(focus_file.split(self.split_flag)[-1], focus_file)

        return map_files

    def match_library_pairs(self, base_datas, other_datas, flag_vrd, model):
        map_files_base = self.split_files_mapping(base_datas, model)
        map_files_other = self.split_files_mapping(other_datas, model)
        base_files, other_files = set(map_files_base.keys()), set(map_files_other.keys())
        common_dump = base_files & other_files
        only_base_dump = base_files - other_files
        only_other_dump = other_files - base_files
        dump_os_changed, dump_exist = [], []
        less_dump, more_dump = only_base_dump, only_other_dump
        so_pattern = re.compile(PAT_SO)
        for other_so in sorted(only_other_dump):
            for base_so in sorted(only_base_dump):
                if base_so in dump_exist:
                    continue
                os_base_name, os_other_name = os.path.basename(base_so), os.path.basename(other_so)
                cut_base_name = re.sub(so_pattern, '', os_base_name)
                cut_other_name = re.sub(so_pattern, '', os_other_name)
                if cut_base_name.lstrip('_') != cut_other_name.lstrip('_'):
                    continue
                full_base_so = map_files_base.get(base_so)
                full_other_so = map_files_other.get(other_so)
                path_result = self.get_version_change_files(base_so, other_so, flag_vrd)
                soname_result = self.get_library_pairs(full_base_so, full_other_so)
                if path_result == CMP_RESULT_CHANGE or soname_result:
                    dump_exist.append(base_so)
                    less_dump.discard(base_so)
                    more_dump.discard(other_so)
                    if model == CMP_TYPE_RPM_ABI:
                        dump_os_changed.append([full_base_so, full_other_so])
                    else:
                        dump_os_changed.append([base_so, other_so])
                    break
        if model == CMP_TYPE_RPM_ABI:
            common_dump = [[map_files_base.get(x), map_files_other.get(x)] for x in common_dump]
            common_dump.extend(dump_os_changed)
            return common_dump

        return [
            [[x, x, CMP_RESULT_SAME] for x in common_dump],
            [self.judge_changed_type(x, flag_vrd) for x in dump_os_changed],
            [[x, '', CMP_RESULT_LESS] for x in less_dump],
            [['', x, CMP_RESULT_MORE] for x in more_dump]
        ]

    def format_dump_provides(self, datas_a, datas_b, flag_v_r_d):
        common_files, common_file_a, common_file_b = [], [], []
        sides_a = self.pretty_provide_datas(datas_a, flag_v_r_d[0])
        sides_b = self.pretty_provide_datas(datas_b, flag_v_r_d[1])
        for k_a in sides_a.keys():
            if sides_b.get(k_a):
                pvds_a = sorted(sides_a.get(k_a))
                pvds_b = sorted(sides_b.get(k_a))
                common_files.append([','.join(pvds_a), ','.join(pvds_b), CMP_RESULT_SAME])
                common_file_a.extend(pvds_a)
                common_file_b.extend(pvds_b)

        all_components_a = self.component_new_provide(datas_a)
        all_components_b = self.component_new_provide(datas_b)
        only_file_a = all_components_a - set(common_file_a)
        only_file_b = all_components_b - set(common_file_b)

        all_dump = [
            common_files,
            [[x, '', CMP_RESULT_LESS] for x in only_file_a],
            [['', x, CMP_RESULT_MORE] for x in only_file_b]
        ]

        return all_dump

    def prase_version(self, version):
        """
        eg:java-1.8.0-openjdk-src-1.8.0.252.b09-2.el8_1.x86_64.rpm
        Compare the differences of the version number in descending order.
        """
        prase_result = []
        m = re.match(r'(\w+)\.?(\w*)\.?(\w*)\.?(\w*)\.?(\w*)', version)
        if m:
            for i in range(1, 6):
                v = m.group(i)
                if v:
                    if v.isdigit():
                        v = self.handle_digit_type(v)
                    elif v.isalpha():
                        # Version for all letter type by '0'.
                        v = '0'
                    else:
                        # Alpha and numver in version:lldpad-1.0.1-13.git036e314.el8.x86_64.rpm,compare by numbers.
                        v = re.sub(r'[a-zA-Z_]+', '', v)[:5]
                else:
                    v = '0'
                prase_result.append(v)

        return prase_result

    def cmp_version(self, v_a, v_b):
        va_list = self.prase_version(v_a)
        vb_list = self.prase_version(v_b)
        cmp_similar = ''
        for i in range(5):
            differences = ''
            if va_list[i] == '0' and vb_list[i] == '0':
                continue
            # time in version:hunspell-pl-0.20180707-1.el8.noarch.rpm,calculate the time difference by time type.
            if isinstance(va_list[i], datetime) and isinstance(vb_list[i], datetime):
                differences = str(abs((vb_list[i] - va_list[i]).days)).rjust(5, '0')
            elif isinstance(va_list[i], str) and isinstance(vb_list[i], str):
                differences = str(abs(int(vb_list[i]) - int(va_list[i]))).rjust(5, '0')
            cmp_similar += differences
        return cmp_similar

    def calculate_rpm_similarity(self, side_a, side_b):
        """
          RPM should keep the arch consistent,version、release comparison is performed by bit-by-bit resolution of the
        contrast gap,dist compare string similarity.
        """
        _, v_a, r_a, d_a, a_a = RPMProxy.rpm_n_v_r_d_a(side_a)
        _, v_b, r_b, d_b, a_b = RPMProxy.rpm_n_v_r_d_a(side_b)
        v_diff = self.cmp_version(v_a, v_b)
        r_diff = self.cmp_version(r_a, r_b)
        d_similar = self.get_equal_rate(d_a, d_b)

        return a_a == a_b, int(v_diff + r_diff) + d_similar

    def get_similar_rpm_pairs(self, base_sides, other_sides):
        """
        Find the RPM pair in sides_a with the closest version based on sides_b.
        :param sides_a, other_sides:Contains multiple RPM package names (list) or dumper (dict).
        """
        cmp_result = filter(lambda dumper: len(dumper) > 1, [base_sides, other_sides])
        if not list(cmp_result):
            return zip(base_sides, other_sides)

        cmp_results = []
        for dump_b in other_sides:
            single_result = []
            similarity_rate = 0
            for dump_a in base_sides:
                rpm_a = dump_a if isinstance(dump_a, str) else dump_a.get('rpm')
                rpm_b = dump_b if isinstance(dump_b, str) else dump_b.get('rpm')
                arch_result, rpm_name_similar = self.calculate_rpm_similarity(rpm_a, rpm_b)
                if not arch_result:
                    continue
                if not single_result or similarity_rate > rpm_name_similar:
                    single_result = [dump_a, dump_b]
                    similarity_rate = rpm_name_similar
                elif similarity_rate == rpm_name_similar:
                    for exist_result in cmp_results:
                        if single_result[0] in exist_result:
                            single_result = [dump_a, dump_b]
            cmp_results.append(single_result)

        return cmp_results

    @abstractmethod
    def run(self):
        pass
