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
import difflib
from abc import ABC, abstractmethod
from datetime import datetime

from oecp.proxy.rpm_proxy import RPMProxy
from oecp.result.compare_result import CMP_RESULT_MORE, CMP_RESULT_LESS, CMP_RESULT_SAME, CMP_RESULT_DIFF, \
    CMP_RESULT_CHANGE

# 两者category指定的级别不同或者未指定
from oecp.result.constants import OLD_CHAR, NEW_CHAR, CMP_SAME_RESULT, CMP_TYPE_KCONFIG

CPM_CATEGORY_DIFF = 4


class CompareExecutor(ABC):

    def __init__(self, dump_a, dump_b, config):
        self.dump_a = dump_a
        self.dump_b = dump_b
        self.config = config

    @staticmethod
    def get_version_change_files(side_a_file, side_b_file, o_char=None, n_char=None):
        side_a_floders = side_a_file.split('/')
        side_b_floders = side_b_file.split('/')
        compare_result = CMP_RESULT_SAME
        if len(side_a_floders) == len(side_b_floders):
            for index in range(1, len(side_a_floders) - 1):
                floder_a = side_a_floders[index]
                floder_b = side_b_floders[index]
                if floder_a == floder_b:
                    continue
                elif floder_a.split(o_char) == floder_b.split(n_char):
                    continue
                elif re.search('\\d+\\.\\d+', side_a_floders[index]) and re.search('\\d+\\.\\d+',
                                                                                   side_b_floders[index]):
                    compare_result = CMP_RESULT_CHANGE
                    continue
                else:
                    compare_result = CMP_RESULT_DIFF
                    break
            return compare_result

    def find_dir_version_change_files(self, only_dump_a, only_dump_b, change_dump, common_dump_add):
        dict_a, dict_b = {}, {}
        for side_a_file in list(only_dump_a):
            dict_a[os.path.basename(side_a_file)] = side_a_file
        for side_b_file in list(only_dump_b):
            dict_b[os.path.basename(side_b_file)] = side_b_file
        for single_key in dict_a.keys():
            if dict_b.get(single_key):
                side_a_file = dict_a.get(single_key)
                side_b_file = dict_b.get(single_key)
                get_result = self.get_version_change_files(side_a_file, side_b_file)
                if get_result == CMP_RESULT_CHANGE:
                    change_dump.append([side_a_file, side_b_file])
                    only_dump_a.discard(side_a_file)
                    only_dump_b.discard(side_b_file)
                elif get_result == CMP_RESULT_SAME:
                    common_dump_add.append([side_a_file, side_b_file])
                    only_dump_a.discard(side_a_file)
                    only_dump_b.discard(side_b_file)
        return [only_dump_a, only_dump_b, change_dump, common_dump_add]

    def format_dump(self, data_a, data_b):
        dump_set_a, dump_set_b = set(data_a), set(data_b)
        common_dump = dump_set_a & dump_set_b
        only_dump_a = dump_set_a - dump_set_b
        only_dump_b = dump_set_b - dump_set_a
        change_dump, common_dump_add = [], []
        only_dump_a, only_dump_b, change_dump, common_dump_add = self.find_dir_version_change_files(
            only_dump_a, only_dump_b, change_dump, common_dump_add)

        for side_a_file in list(only_dump_a):
            for side_b_file in list(only_dump_b):
                get_result = ''
                file_a, file_b = os.path.basename(side_a_file), os.path.basename(side_b_file)
                # 识别so库文件两种版本变化形式
                if file_a.endswith('.so') and file_b.endswith('.so'):
                    file_a_version_1 = re.search('\\d+\\.\\d+', file_a.split('-')[-1])
                    file_b_version_1 = re.search('\\d+\\.\\d+', file_a.split('-')[-1])
                    if file_a_version_1 and file_b_version_1 and file_a.split('-')[0] == file_b.split('-')[0]:
                        get_result = self.get_version_change_files(side_a_file, side_b_file)
                elif file_a.split('.so.')[0] == file_b.split('.so.')[0]:
                    file_a_version_2 = re.search('\\d+\\.\\d+\\.\\d+', file_a.split('.so.')[-1])
                    file_b_version_2 = re.search('\\d+\\.\\d+\\.\\d+', file_a.split('.so.')[-1])
                    if file_a_version_2 and file_b_version_2:
                        get_result = self.get_version_change_files(side_a_file, side_b_file)
                # 识别rpm文件、文件夹名称中发行商字样变更
                for o_char in OLD_CHAR:
                    for n_char in NEW_CHAR[o_char]:
                        if file_a.split(o_char) == file_b.split(n_char):
                            get_result = self.get_version_change_files(side_a_file, side_b_file, o_char, n_char)

                if get_result == CMP_RESULT_CHANGE:
                    change_dump.append([side_a_file, side_b_file])
                    only_dump_a.discard(side_a_file)
                    only_dump_b.discard(side_b_file)
                    break
                elif get_result == CMP_RESULT_SAME:
                    common_dump_add.append([side_a_file, side_b_file])
                    only_dump_a.discard(side_a_file)
                    only_dump_b.discard(side_b_file)
                    break
        all_dump = [
            [[x, x, CMP_RESULT_SAME] for x in common_dump],
            [[x[0], x[1], CMP_RESULT_CHANGE] for x in change_dump],
            [[x, '', CMP_RESULT_LESS] for x in only_dump_a],
            [['', x, CMP_RESULT_MORE] for x in only_dump_b]
        ]
        if common_dump_add:
            for common_cmp_pair in common_dump_add:
                all_dump[0].append([common_cmp_pair[0], common_cmp_pair[1], CMP_RESULT_SAME])
        return all_dump

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
                    if cmp_result == CMP_RESULT_CHANGE:
                        common_file_pairs.append([file_a, file_b])
                        common_file_a.append(file_a)
                        common_file_b.append(file_b)
        only_file_a = list(set(files_a) - set(common_file_a))
        only_file_b = list(set(files_b) - set(common_file_b))
        return common_file_pairs, only_file_a, only_file_b

    @staticmethod
    def format_dump_file(data_a, data_b):
        dump_set_a, dump_set_b = set(data_a), set(data_b)
        common_dump = dump_set_a & dump_set_b
        only_dump_a = dump_set_a - dump_set_b
        only_dump_b = dump_set_b - dump_set_a
        all_dump = [
            [[x, x, CMP_RESULT_SAME] for x in common_dump],
            [[x, '', CMP_RESULT_LESS] for x in only_dump_a],
            [['', x, CMP_RESULT_MORE] for x in only_dump_b]
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
        same_pairs = []
        same_in_a, same_in_b = [], []
        for rpm_a in data_a:
            for rpm_b in data_b:
                if RPMProxy.rpm_name(rpm_a) == RPMProxy.rpm_name(rpm_b):
                    same_pairs.append([rpm_a, rpm_b, CMP_RESULT_SAME])
                    same_in_a.append(rpm_a)
                    same_in_b.append(rpm_b)
        less_result = data_a - set(same_in_a)
        more_result = data_b - set(same_in_b)
        all_dump = [
            same_pairs,
            [[x, '', CMP_RESULT_LESS] for x in less_result],
            [['', x, CMP_RESULT_MORE] for x in more_result]
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
                losted.append([' '.join([k, "=", va]), '', 'losted'])
            elif va == vb:
                same.append([' '.join([k, "=", va]), ' '.join([k, "=", vb]), 'same'])
            else:
                changed.append([' '.join([k, "=", va]), ' '.join([k, "=", vb]), 'changed'])
        all_dump.append(same)
        all_dump.append(changed)
        all_dump.append(losted)
        if changed or losted:
            file_result = CMP_RESULT_DIFF
        return file_result, all_dump

    @staticmethod
    def get_equal_rate(dist_a, dist_b):
        return 1 - difflib.SequenceMatcher(None, dist_a, dist_b).quick_ratio()

    @staticmethod
    def _cmp_rpm_arch(arch_a, arch_b):
        # Check the arch of RPM packages is consistent or not.
        if arch_a == arch_b:
            return True
        return False

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

    def count_cmp_result(self, count_result, cmp_result):
        if cmp_result in CMP_SAME_RESULT:
            count_result["same"] += 1
        elif cmp_result == CMP_RESULT_LESS:
            count_result["less"] += 1
        elif cmp_result == CMP_RESULT_MORE:
            count_result["more"] += 1
        elif cmp_result == CMP_RESULT_DIFF:
            count_result["diff"] += 1

    @abstractmethod
    def run(self):
        pass
