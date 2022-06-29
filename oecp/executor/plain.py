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
from oecp.proxy.rpm_proxy import RPMProxy
from oecp.result.compare_result import CMP_RESULT_SAME, CompareResultComposite, CMP_TYPE_RPM, CMP_TYPE_RPM_CONFIG, \
    CompareResultComponent, CMP_RESULT_DIFF, CMP_RESULT_EXCEPTION, CMP_RESULT_LESS, CMP_RESULT_MORE
from oecp.result.constants import DETAIL_PATH
from oecp.utils.shell import shell_cmd

logger = logging.getLogger('oecp')


class PlainCompareExecutor(CompareExecutor):

    def __init__(self, dump_a, dump_b, config):
        super(PlainCompareExecutor, self).__init__(dump_a, dump_b, config)
        self.dump_a = dump_a.run()
        self.dump_b = dump_b.run()
        cache_require_key = 'extract'
        self._work_dir = self.config.get(cache_require_key, {}).get('work_dir', DETAIL_PATH)
        self.data = 'data'
        self.lack_conf_flag = False

    @staticmethod
    def _save_diff_result(file_path, content):
        with open(file_path, "w") as f:
            f.write(content)

    def _compare_result(self, dump_a, dump_b, single_result=CMP_RESULT_SAME):
        count_result = {'more_count': 0, 'less_count': 0, 'diff_count': 0}
        category = dump_a['category'] if dump_a['category'] == dump_b[
            'category'] else CPM_CATEGORY_DIFF
        kind = dump_a['kind']
        result = CompareResultComposite(CMP_TYPE_RPM, single_result, dump_a['rpm'], dump_b['rpm'], category)
        verbose_diff_path = f'{dump_a["rpm"]}__diff__{dump_b["rpm"]}'
        dump_a_files = dump_a[self.data]
        dump_b_files = dump_b[self.data]
        common_file_pairs, only_file_a, only_file_b = self.split_common_files(dump_a_files, dump_b_files)
        base_dir = os.path.join(self._work_dir, kind, verbose_diff_path)
        for pair in common_file_pairs:
            cmd = "diff -uN {} {}".format(pair[0], pair[1])
            ret, out, err = shell_cmd(cmd.split())
            base_a = os.path.basename(pair[0])
            base_b = os.path.basename(pair[1])
            for compare_line in out.split('\n')[3:]:
                if compare_line:
                    lack_conf = re.match('-', compare_line)
                    openEuler_conf = re.search('openEuler', compare_line)
                    if lack_conf and not openEuler_conf:
                        self.lack_conf_flag = True
                        break
            if ret and out and self.lack_conf_flag:
                try:
                    # 替换diff中的文件名
                    out = re.sub("---\s+\S+\s+", "--- {} ".format(pair[0]), out)
                    out = re.sub("\+\+\+\s+\S+\s+", "+++ {} ".format(pair[1]), out)
                    if not os.path.exists(base_dir):
                        os.makedirs(base_dir)
                    file_path = os.path.join(base_dir,
                                             "%s__diff__%s" % (base_a, base_b))
                    self._save_diff_result(file_path, out)
                    logger.info("plain files are diff")
                    data = CompareResultComponent(
                        CMP_TYPE_RPM_CONFIG, CMP_RESULT_DIFF, base_a, base_b, file_path)
                    count_result["diff_count"] += 1
                    result.set_cmp_result(CMP_RESULT_DIFF)
                except IOError:
                    logger.exception("save compare result exception")
                    data = CompareResultComponent(
                        CMP_TYPE_RPM_CONFIG, CMP_RESULT_EXCEPTION, base_a, base_b)
            else:
                data = CompareResultComponent(
                    CMP_TYPE_RPM_CONFIG, CMP_RESULT_SAME, base_a, base_b)
            result.add_component(data)
        if only_file_a:
            for file_a in only_file_a:
                data = CompareResultComponent(CMP_TYPE_RPM_CONFIG, CMP_RESULT_LESS, os.path.basename(file_a), '')
                result.add_component(data)
                count_result["less_count"] += 1
        if only_file_b:
            for file_b in only_file_b:
                data = CompareResultComponent(CMP_TYPE_RPM_CONFIG, CMP_RESULT_MORE, '', os.path.basename(file_b))
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
