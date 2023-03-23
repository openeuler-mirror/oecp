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

import logging
import os
import re
import chardet

from oecp.executor.base import CompareExecutor, CPM_CATEGORY_DIFF
from oecp.result.compare_result import CompareResultComposite, CompareResultComponent
from oecp.result.constants import *
from oecp.utils.shell import shell_cmd

logger = logging.getLogger('oecp')


class HeaderCompareExecutor(CompareExecutor):

    def __init__(self, dump_a, other_dump, config):
        super(HeaderCompareExecutor, self).__init__(dump_a, other_dump, config)
        self.dump_a = dump_a.run()
        self.dump_b = other_dump.run()
        self.data = 'data'
        self.lack_conf_flag = False

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
                new_contents = re.sub("/\\*[\\s\\S]*?\\*/|//.*", "", contents)
                file_bak.write(new_contents)
                os.remove(file_path)
                os.rename("%s.bak" % file_path, file_path)
        except (IOError, UnicodeDecodeError, OSError, FileNotFoundError):
            logger.exception("an error occurred while removing the contents of the file")

    def compare_result(self, base_dump, other_dump, single_result=CMP_RESULT_SAME):
        count_result = {'same': 0, 'more': 0, 'less': 0, 'diff': 0}
        category = base_dump['category'] if base_dump['category'] == other_dump['category'] else CPM_CATEGORY_DIFF
        result = CompareResultComposite(CMP_TYPE_RPM, single_result, base_dump['rpm'], other_dump['rpm'], category)
        map_files_a = self.split_files_mapping(base_dump[self.data])
        map_files_b = self.split_files_mapping(other_dump[self.data])
        flag_v_r_d = self.extract_version_flag(base_dump['rpm'], other_dump['rpm'])
        common_file_pairs, only_base_files, only_other_files = self.format_fullpath_files(map_files_a, map_files_b,
                                                                                          flag_v_r_d)
        if not common_file_pairs and not only_base_files and not only_other_files:
            logger.debug(f"No header package found, ignored with {other_dump['rpm']} and {other_dump['rpm']}")
            return result
        for pair in common_file_pairs:
            self._exclude_comments(pair[0])
            self._exclude_comments(pair[1])
            cmd = "diff -uBHN {} {}".format(pair[0], pair[1])
            ret, out, err = shell_cmd(cmd.split())
            base_file_path = pair[0].split(self.split_flag)[-1]
            other_file_path = pair[1].split(self.split_flag)[-1]
            for compare_line in out.split('\n')[3:]:
                if compare_line:
                    lack_conf = re.match('-', compare_line)
                    openeuler_conf = re.search('openEuler', compare_line)
                    if lack_conf and not openeuler_conf:
                        self.lack_conf_flag = True
                        break
            if ret and out and self.lack_conf_flag:
                try:
                    # 替换diff中的文件名
                    out = re.sub("---\\s+\\S+\\s+", "--- {} ".format(pair[0]), out)
                    out = re.sub("\\+\\+\\+\\s+\\S+\\s+", "+++ {} ".format(pair[1]), out)
                    self.count_cmp_result(count_result, CMP_RESULT_DIFF)
                    data = CompareResultComponent(
                        CMP_TYPE_RPM_HEADER, CMP_RESULT_DIFF, base_file_path, other_file_path, detail_file=out)
                    result.set_cmp_result(CMP_RESULT_DIFF)
                except IOError:
                    logger.exception("save compare result exception")
                    data = CompareResultComponent(
                        CMP_TYPE_RPM_HEADER, CMP_RESULT_EXCEPTION, base_file_path, other_file_path)
            else:
                self.count_cmp_result(count_result, CMP_RESULT_SAME)
                data = CompareResultComponent(CMP_TYPE_RPM_HEADER, CMP_RESULT_SAME, base_file_path, other_file_path)
            result.add_component(data)
        for base_file in only_base_files:
            self.count_cmp_result(count_result, CMP_RESULT_LESS)
            data = CompareResultComponent(CMP_TYPE_RPM_HEADER, CMP_RESULT_LESS, base_file, '')
            result.add_component(data)
        for other_file in only_other_files:
            self.count_cmp_result(count_result, CMP_RESULT_MORE)
            data = CompareResultComponent(CMP_TYPE_RPM_HEADER, CMP_RESULT_MORE, '', other_file)
            result.add_component(data)
        result.add_count_info(count_result)

        return result

    def compare(self):
        compare_list = []
        similar_dumpers = self.get_similar_rpm_pairs(self.dump_a, self.dump_b)
        for single_pair in similar_dumpers:
            if single_pair:
                base_dump, other_dump = single_pair[0], single_pair[1]
                result = self.compare_result(base_dump, other_dump)
                compare_list.append(result)
        return compare_list

    def run(self):
        result = self.compare()
        return result
