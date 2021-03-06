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
from abc import ABC, abstractmethod
from oecp.proxy.rpm_proxy import RPMProxy
from oecp.result.compare_result import CMP_RESULT_MORE, CMP_RESULT_LESS, CMP_RESULT_SAME, CMP_RESULT_DIFF, \
    CMP_RESULT_CHANGE

# 两者category指定的级别不同或者未指定
from oecp.result.constants import OLD_CHAR, NEW_CHAR

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
        compare_result = 'same'
        if len(side_a_floders) == len(side_b_floders):
            for index in range(1, len(side_a_floders) - 1):
                floder_a = side_a_floders[index]
                floder_b = side_b_floders[index]
                if floder_a == floder_b:
                    continue
                elif floder_a.split(o_char) == floder_b.split(n_char):
                    continue
                elif re.search('\d+\.\d+', side_a_floders[index]) and re.search('\d+\.\d+', side_b_floders[index]):
                    compare_result = "change"
                    continue
                else:
                    compare_result = 'diff'
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
                if get_result == "change":
                    change_dump.append([side_a_file, side_b_file])
                    only_dump_a.discard(side_a_file)
                    only_dump_b.discard(side_b_file)
                elif get_result == "same":
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
                    file_a_version_1 = re.search('\d+\.\d+', file_a.split('-')[-1])
                    file_b_version_1 = re.search('\d+\.\d+', file_a.split('-')[-1])
                    if file_a_version_1 and file_b_version_1 and file_a.split('-')[0] == file_b.split('-')[0]:
                        get_result = self.get_version_change_files(side_a_file, side_b_file)
                elif file_a.split('.so.')[0] == file_b.split('.so.')[0]:
                    file_a_version_2 = re.search('\d+\.\d+\.\d+', file_a.split('.so.')[-1])
                    file_b_version_2 = re.search('\d+\.\d+\.\d+', file_a.split('.so.')[-1])
                    if file_a_version_2 and file_b_version_2:
                        get_result = self.get_version_change_files(side_a_file, side_b_file)
                # 识别rpm文件、文件夹名称中发行商字样变更
                for o_char in OLD_CHAR:
                    for n_char in NEW_CHAR[o_char]:
                        if file_a.split(o_char) == file_b.split(n_char):
                            get_result = self.get_version_change_files(side_a_file, side_b_file, o_char, n_char)

                if get_result == "change":
                    change_dump.append([side_a_file, side_b_file])
                    only_dump_a.discard(side_a_file)
                    only_dump_b.discard(side_b_file)
                    break
                elif get_result == "same":
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

    @staticmethod
    def split_common_files(files_a, files_b):
        common_file_pairs, common_file_a, common_file_b = [], [], []
        for file_a in files_a:
            for file_b in files_b:
                if file_a.split('__rpm__')[-1] == file_b.split('__rpm__')[-1]:
                    common_file_pairs.append([file_a, file_b])
                    common_file_a.append(file_a)
                    common_file_b.append(file_b)
        only_file_a = list(set(files_a) - set(common_file_a))
        only_file_b = list(set(files_b) - set(common_file_b))
        return common_file_pairs, only_file_a, only_file_b

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
                less.append([va, '', 'less'])
            elif va == vb:
                same.append([va, vb, 'same'])
            else:
                diff.append([va, vb, 'diff'])

        all_dump.append(same)
        all_dump.append(diff)
        all_dump.append(less)

        if kind == 'kconfig':
            more = []
            for k, vb, in h_b.items():
                va = h_a.get(k, None)
                if va is None:
                    more.append(['', vb, 'more'])

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

    @abstractmethod
    def run(self):
        pass
