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
from oecp.result.compare_result import CMP_RESULT_MORE, CMP_RESULT_LESS, CMP_RESULT_SAME, CMP_RESULT_DIFF, \
    CMP_RESULT_CHANGE

# 两者category指定的级别不同或者未指定
from oecp.result.constants import STAND_DISTS, CMP_SAME_RESULT, CMP_TYPE_KCONFIG, BASE_SIDE, OSV_SIDE

CPM_CATEGORY_DIFF = 4

logger = logging.getLogger('oecp')


class CompareExecutor(ABC):

    def __init__(self, dump_a, dump_b, config):
        self.dump_a = dump_a
        self.dump_b = dump_b
        self.config = config
        self.split_flag = '__rpm__'

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
    def format_service_detail(data_a, data_b):
        same = []
        changed = []
        losted = []
        all_dump = []
        file_result = CMP_RESULT_SAME
        for k, va in data_a.items():
            vb = data_b.get(k, None)
            if vb is None:
                losted.append([' '.join([k, "=", va]), '', CMP_RESULT_LESS])
            elif va == vb:
                same.append([' '.join([k, "=", va]), ' '.join([k, "=", vb]), CMP_RESULT_SAME])
            else:
                changed.append([' '.join([k, "=", va]), ' '.join([k, "=", vb]), CMP_RESULT_CHANGE])
        all_dump.append(same)
        all_dump.append(changed)
        all_dump.append(losted)
        if changed or losted:
            file_result = CMP_RESULT_DIFF
        return file_result, all_dump

    @staticmethod
    def count_cmp_result(count_result, cmp_result):
        if cmp_result in CMP_SAME_RESULT:
            count_result["same"] += 1
        elif cmp_result == CMP_RESULT_LESS:
            count_result["less"] += 1
        elif cmp_result == CMP_RESULT_MORE:
            count_result["more"] += 1
        elif cmp_result == CMP_RESULT_DIFF:
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
    def _cmp_rpm_arch(arch_a, arch_b):
        # Check the arch of RPM packages is consistent or not.
        if arch_a == arch_b:
            return True
        return False

    @staticmethod
    def get_version_change_files(side_a_file, side_b_file, flag_v=None):
        side_a_floders = side_a_file.split('/')
        side_b_floders = side_b_file.split('/')
        compare_result = CMP_RESULT_CHANGE
        if len(side_a_floders) == len(side_b_floders):
            for index in range(1, len(side_a_floders) - 1):
                floder_a = side_a_floders[index]
                floder_b = side_b_floders[index]
                if floder_a == floder_b:
                    continue
                elif floder_a.split(STAND_DISTS.get(BASE_SIDE)) == floder_b.split(STAND_DISTS.get(OSV_SIDE)):
                    continue
                elif flag_v and floder_a.replace(flag_v[0], '') == floder_b.replace(flag_v[1], ''):
                    continue
                elif re.search('\\d+\\.\\d+', floder_a) and re.search('\\d+\\.\\d+', floder_b):
                    continue
                else:
                    compare_result = CMP_RESULT_DIFF
                    break
            return compare_result
        else:
            return CMP_RESULT_DIFF

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
            # so动态库
            so_version = re.search("(([-.]\\d+){0,3}\\.so([-.]\\d+){0,3})\\((.*?)\\)", pvd_name)
            if so_version:
                component_so_name = pvd_name.split(so_version.group(1))[0] + so_version.group(4)
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
    def mapping_files(files, flag):
        map_result = {}
        for file in files:
            pat_other = re.compile(r"(\d+\.\d+\.\d+)|(\d+\.\d+)|(v\d{8}-\d{4})")
            simple_file = file.replace(flag, '')
            remove_version_file = re.sub(pat_other, '', simple_file)
            map_result.setdefault(remove_version_file, file)

        return map_result

    def format_dump(self, data_a, data_b, flag_v_r_d):
        """
        抓取相对路径相同或版本变化的文件对
        @param data_a: dump_a获取的文件全路径
        @param data_b: dump_b获取的文件全路径
        @param flag_v_r_d: version+release+dist标识
        @return: 返回相对路径
        """
        set_files_a = set([f.split(self.split_flag)[-1] for f in data_a])
        set_files_b = set([f.split(self.split_flag)[-1] for f in data_b])
        common_dump, change_dump, only_a, only_b = self.format_changed_files(set_files_a, set_files_b, flag_v_r_d)
        all_dump = [
            [[x, x, CMP_RESULT_SAME] for x in common_dump],
            [[x[0], x[1], CMP_RESULT_CHANGE] for x in change_dump],
            [[x, '', CMP_RESULT_LESS] for x in only_a],
            [['', x, CMP_RESULT_MORE] for x in only_b]
        ]

        return all_dump

    def format_fullpath_files(self, data_a, data_b, flag_v_r_d):
        """
        抓取相对路径相同或版本变化的文件对
        @param data_a: 相对路径与文件绝对能路径映射
        @param data_b: 同上
        @param flag_v_r_d:
        @return: 返回绝对路径
        """
        set_files_a, set_files_b = set(data_a.keys()), set(data_b.keys())
        common_dump, change_dump, only_a, only_b = self.format_changed_files(set_files_a, set_files_b, flag_v_r_d)
        common_pairs = [[data_a.get(y), data_b.get(y)] for y in common_dump]
        common_pairs.extend([[data_a.get(y[0]), data_b.get(y[1])] for y in change_dump])

        return common_pairs, only_a, only_b

    def format_changed_files(self, dump_set_a, dump_set_b, flag_v_r_d):
        """
        识别文件路径、文件名中存在以rpm包（version+release+dist/dist标识/x.x.x版本号）命名的相同文件对
        @param dump_set_a: 缺失文件
        @param dump_set_b: 新增文件
        @param flag_v_r_d: version+release+dist标识
        """
        common_dump = dump_set_a & dump_set_b
        only_dump_a = dump_set_a - dump_set_b
        only_dump_b = dump_set_b - dump_set_a
        change_dump = []

        datas_a = self.mapping_files(only_dump_a, flag_v_r_d[0])
        datas_b = self.mapping_files(only_dump_b, flag_v_r_d[1])
        """
        eg: /usr/src/kernels/6.1.6-1.0.0.3.oe1.aarch64
            /usr/src/kernels/6.1.8-1.0.0.5.oe1.aarch64
        """
        for simple_a in datas_a.keys():
            if datas_b.get(simple_a):
                file_a = datas_a.get(simple_a)
                file_b = datas_b.get(simple_a)
                change_dump.append([file_a, file_b])
                only_dump_a.discard(file_a)
                only_dump_b.discard(file_b)

        for side_a_file in list(only_dump_a):
            for side_b_file in list(only_dump_b):
                get_result = CMP_RESULT_DIFF
                so_pattern = re.compile(r"(([-.]\d+){0,3}\.so([-.]\d+){0,3})|-[a-z0-9]{16}.so")
                file_a, file_b = os.path.basename(side_a_file), os.path.basename(side_b_file)
                so_version_a = re.search(so_pattern, file_a)
                so_version_b = re.search(so_pattern, file_b)
                if file_a == file_b or file_a.split(STAND_DISTS.get(BASE_SIDE)) == file_b.split(
                        STAND_DISTS.get(OSV_SIDE)):
                    get_result = self.get_version_change_files(side_a_file, side_b_file)
                # 识别so库文件版本变化
                elif so_version_a and so_version_b:
                    so_name_a = file_a.split(so_version_a.group())[0]
                    so_name_b = file_b.split(so_version_b.group())[0]
                    if so_name_a == so_name_b:
                        get_result = self.get_version_change_files(side_a_file, side_b_file)

                if get_result == CMP_RESULT_CHANGE:
                    change_dump.append([side_a_file, side_b_file])
                    only_dump_a.discard(side_a_file)
                    only_dump_b.discard(side_b_file)
                    break

        return common_dump, change_dump, only_dump_a, only_dump_b

    def split_files_mapping(self, dump_files):
        map_files = {}
        for file in dump_files:
            map_files.setdefault(file.split(self.split_flag)[-1], file)

        return map_files

    def split_common_files(self, files_a, files_b):
        common_file_pairs, common_file_a, common_file_b = [], [], []
        for file_a in files_a:
            for file_b in files_b:
                path_a, path_b = file_a.split('__rpm__')[-1], file_b.split('__rpm__')[-1]
                if path_a == path_b:
                    common_file_pairs.append([file_a, file_b])
                    common_file_a.append(file_a)
                    common_file_b.append(file_b)
                elif os.path.basename(path_a) == os.path.basename(path_b):
                    cmp_result = self.get_version_change_files(path_a, path_b)
                    if cmp_result in CMP_SAME_RESULT:
                        common_file_pairs.append([file_a, file_b])
                        common_file_a.append(file_a)
                        common_file_b.append(file_b)
        only_file_a = list(set(files_a) - set(common_file_a))
        only_file_b = list(set(files_b) - set(common_file_b))
        return common_file_pairs, only_file_a, only_file_b

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
        arch_result = self._cmp_rpm_arch(a_a, a_b)
        v_diff = self.cmp_version(v_a, v_b)
        r_diff = self.cmp_version(r_a, r_b)
        d_similar = self.get_equal_rate(d_a, d_b)
        return arch_result, int(v_diff + r_diff) + d_similar

    def get_similar_rpm_pairs(self, sides_a, sides_b):
        """
        Find the RPM pair in sides_a with the closest version based on sides_b.
        :param sides_a, sides_b:Contains multiple RPM package names (list) or dumper (dict).
        """
        cmp_results = []
        for dump_b in sides_b:
            single_result = []
            similarity_rate = 0
            for dump_a in sides_a:
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
