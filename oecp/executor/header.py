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
import chardet

from oecp.executor.base import CompareExecutor, CPM_CATEGORY_DIFF
from oecp.proxy.rpm_proxy import RPMProxy
from oecp.result.compare_result import CompareResultComposite, CompareResultComponent
from oecp.result.constants import CMP_TYPE_RPM_KERNEL, CMP_TYPE_RPM_HEADER, CMP_RESULT_DIFF, CMP_RESULT_EXCEPTION, \
    CMP_RESULT_SAME, CMP_TYPE_RPM, CMP_RESULT_LESS, CMP_RESULT_MORE
from oecp.utils.shell import shell_cmd

logger = logging.getLogger('oecp')


class HeaderCompareExecutor(CompareExecutor):

    def __init__(self, dump_a, dump_b, config):
        super(HeaderCompareExecutor, self).__init__(dump_a, dump_b, config)
        self.dump_a = dump_a.run()
        self.dump_b = dump_b.run()
        self._work_dir = self.config.get('detail_path')

    @staticmethod
    def _save_diff_result(file_path, content):
        with open(file_path, "w") as f:
            f.write(content)

    @staticmethod
    def _get_file_encoding_format(file_path):
        """
        get the encoding format of the file
        Args:
            file_path: file_path

        Returns:
            file_type: file encoding format
        """
        with open(file_path, "rb") as file:
            contents = file.read()
            file_type = chardet.detect(contents)['encoding']
            return file_type

    def _exclude_comments(self, file_path):
        """
        remove the comments from the header file and
        save it in the original file format
        Args:
            file_path: file_path

        Returns:
            None
        """
        try:
            file_format = self._get_file_encoding_format(file_path)
            with open(file_path, "r", encoding=file_format,
                      errors='ignore') as file, open("%s.bak" % file_path,
                                                     "w",
                                                     encoding=file_format) as file_bak:
                contents = file.read()
                # use regex to exclude comments in matching header files
                # comment examples /* xxxxxx*/ and //
                new_contents = re.sub(r"/\*[\s\S]*?\*/|//.*", "", contents)
                file_bak.write(new_contents)
                os.remove(file_path)
                os.rename("%s.bak" % file_path, file_path)
        except (UnicodeDecodeError, OSError):
            logger.exception("an error occurred while removing the contents of the file")

    def no_check_detail_info(self, dump):
        """
        内核不比较相同头文件，仅计算增删文件
        @param dump:
        @return:
        """

        src_name = RPMProxy.rpm_name(dump['src_pkg'])

        return self.config.get('no_detail') and src_name == CMP_TYPE_RPM_KERNEL

    def count_header_difference(self, pair, base_dir, result, count_result):
        self._exclude_comments(pair[0])
        self._exclude_comments(pair[1])
        cmd = "diff -uBHN {} {}".format(pair[0], pair[1])
        ret, out, err = shell_cmd(cmd.split())
        base_a = os.path.basename(pair[0])
        base_b = os.path.basename(pair[1])
        lack_conf_flag = self.check_diff_info(out)
        if ret and out and lack_conf_flag:
            try:
                # 替换diff中的文件名
                out = re.sub("---\\s+\\S+\\s+", "--- {} ".format(pair[0]), out)
                out = re.sub("\\+\\+\\+\\s+\\S+\\s+", "+++ {} ".format(pair[1]), out)
                if not os.path.exists(base_dir):
                    os.makedirs(base_dir)
                file_path = os.path.join(base_dir,
                                         "%s__diff__%s" % (base_a, base_b))
                self._save_diff_result(file_path, out)
                data = CompareResultComponent(CMP_TYPE_RPM_HEADER, CMP_RESULT_DIFF, base_a, base_b, file_path)
                count_result["diff_count"] += 1
                result.set_cmp_result(CMP_RESULT_DIFF)
            except IOError:
                logger.exception("save compare result exception")
                data = CompareResultComponent(
                    CMP_TYPE_RPM_HEADER, CMP_RESULT_EXCEPTION, base_a, base_b)
        else:
            data = CompareResultComponent(CMP_TYPE_RPM_HEADER, CMP_RESULT_SAME, base_a, base_b)

        return data

    def _compare_result(self, dump_a, dump_b, single_result=CMP_RESULT_SAME):
        count_result = {'more_count': 0, 'less_count': 0, 'diff_count': 0}
        category = dump_a['category'] if dump_a['category'] == dump_b['category'] else CPM_CATEGORY_DIFF
        kind = dump_a['kind']
        flag_v_r_d = self.extract_version_flag(dump_a['rpm'], dump_b['rpm'])
        result = CompareResultComposite(CMP_TYPE_RPM, single_result, dump_a['rpm'], dump_b['rpm'], category)
        verbose_diff_path = f'{dump_a["rpm"]}__diff__{dump_b["rpm"]}'
        dump_a_files = dump_a[self.data]
        dump_b_files = dump_b[self.data]
        common_file_pairs, only_file_a, only_file_b = self.format_fullpath_files(dump_a_files, dump_b_files, flag_v_r_d)
        base_dir = os.path.join(self._work_dir, kind, verbose_diff_path)

        for pair in common_file_pairs:
            if self.no_check_detail_info(dump_a):
                data = CompareResultComponent(CMP_TYPE_RPM_HEADER, CMP_RESULT_SAME, os.path.basename(pair[0]),
                                              os.path.basename(pair[1]))
            else:
                data = self.count_header_difference(pair, base_dir, result, count_result)
            result.add_component(data)
        if only_file_a:
            for file_a in only_file_a:
                data = CompareResultComponent(CMP_TYPE_RPM_HEADER, CMP_RESULT_LESS, os.path.basename(file_a), '')
                result.add_component(data)
                count_result["less_count"] += 1
        if only_file_b:
            for file_b in only_file_b:
                data = CompareResultComponent(CMP_TYPE_RPM_HEADER, CMP_RESULT_MORE, '', os.path.basename(file_b))
                result.add_component(data)
                count_result["more_count"] += 1
        result.add_count_info(count_result)

        return result

    def compare(self):
        compare_list = []
        for dump_a in self.dump_a:
            for dump_b in self.dump_b:
                # 取rpm name 相同进行比较
                if RPMProxy.rpm_name(dump_a['rpm']) == RPMProxy.rpm_name(dump_b['rpm']):
                    result = self._compare_result(dump_a, dump_b)
                    compare_list.append(result)
        return compare_list

    def run(self):
        result = self.compare()
        return result
