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

from oecp.executor.base import CompareExecutor, CPM_CATEGORY_DIFF
from oecp.result.compare_result import CMP_RESULT_SAME, CompareResultComposite, CMP_TYPE_RPM, CMP_TYPE_RPM_CONFIG, \
    CompareResultComponent, CMP_RESULT_DIFF, CMP_RESULT_EXCEPTION, CMP_RESULT_LESS, CMP_RESULT_MORE
from oecp.utils.shell import shell_cmd

logger = logging.getLogger('oecp')


class PlainCompareExecutor(CompareExecutor):

    def __init__(self, base_dump, other_dump, config):
        super(PlainCompareExecutor, self).__init__(base_dump, other_dump, config)
        self.base_dump = base_dump.run()
        self.other_dump = other_dump.run()
        self.data = 'data'

    def compare_result(self, base_dump, other_dump, single_result=CMP_RESULT_SAME):
        count_result = {'same': 0, 'more': 0, 'less': 0, 'diff': 0}
        category = base_dump['category'] if base_dump['category'] == other_dump['category'] else CPM_CATEGORY_DIFF
        result = CompareResultComposite(CMP_TYPE_RPM, single_result, base_dump['rpm'], other_dump['rpm'], category)
        base_files, other_files = base_dump[self.data], other_dump[self.data]
        flag_vrd = self.extract_version_flag(base_dump['rpm'], other_dump['rpm'])
        common_file_pairs, less_dumps, more_dumps = self.format_fullpath_files(base_files, other_files, flag_vrd)
        if not common_file_pairs and not less_dumps and not more_dumps:
            logger.debug(f"No config package found, ignored with {other_dump['rpm']} and {other_dump['rpm']}")
            return result
        for pair in common_file_pairs:
            cmd = "diff -uN {} {}".format(pair[0], pair[1])
            ret, out, err = shell_cmd(cmd.split())
            base_conf_file = os.path.basename(pair[0])
            other_conf_file = os.path.basename(pair[1])
            lack_conf_flag = self.check_diff_info(out)
            if ret and out and lack_conf_flag:
                try:
                    # 替换diff中的文件名
                    out = re.sub("---\\s+\\S+\\s+", "--- {} ".format(pair[0]), out)
                    out = re.sub("\\+\\+\\+\\s+\\S+\\s+", "+++ {} ".format(pair[1]), out)
                    logger.info("plain files are diff")
                    self.count_cmp_result(count_result, CMP_RESULT_DIFF)
                    data = CompareResultComponent(CMP_TYPE_RPM_CONFIG, CMP_RESULT_DIFF, base_conf_file, other_conf_file,
                                                  detail_file=out)
                    result.set_cmp_result(CMP_RESULT_DIFF)
                except IOError:
                    logger.exception("save compare result exception")
                    data = CompareResultComponent(CMP_TYPE_RPM_CONFIG, CMP_RESULT_EXCEPTION, base_conf_file,
                                                  other_conf_file)
            else:
                self.count_cmp_result(count_result, CMP_RESULT_SAME)
                data = CompareResultComponent(CMP_TYPE_RPM_CONFIG, CMP_RESULT_SAME, base_conf_file, other_conf_file)
            result.add_component(data)

        for base_file in less_dumps:
            self.count_cmp_result(count_result, CMP_RESULT_LESS)
            data = CompareResultComponent(CMP_TYPE_RPM_CONFIG, CMP_RESULT_LESS, base_file, '')
            result.add_component(data)
        for other_file in more_dumps:
            self.count_cmp_result(count_result, CMP_RESULT_MORE)
            data = CompareResultComponent(CMP_TYPE_RPM_CONFIG, CMP_RESULT_MORE, '', other_file)
            result.add_component(data)
        result.add_count_info(count_result)

        return result

    def compare(self):
        compare_list = []
        similar_dumpers = self.get_similar_rpm_pairs(self.base_dump, self.other_dump)
        for single_pair in similar_dumpers:
            if single_pair:
                base_dump, other_dump = single_pair[0], single_pair[1]
                result = self.compare_result(base_dump, other_dump)
                compare_list.append(result)
        return compare_list

    def run(self):
        result = self.compare()
        return result
