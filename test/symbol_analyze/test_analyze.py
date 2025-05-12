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

import os
import sys
sys.path.append('/'.join(os.path.abspath(__file__).split('/')[:-3]))
from unittest import TestCase, main
from oecp.symbol_analyze.controller.symbol_analyze import RpmController
from oecp.symbol_analyze.analyze import RpmAnalyze
from oecp.db.symbol_temporary import SymbolTemporary
from oecp.db.pull_request import PullRequest
from oecp.main.factory import Factory
from oecp.db.symbol import Symbol

BRANCH_NAME = 'unit_test'
DB_PASSWORC = ''
PR_ID = '123456'


def fake_args():
    class Args():
        pass
    args = Args()
    args.work_dir = os.path.dirname(__file__)
    args.symbol = 'unit_test'
    args.pr_id = PR_ID
    args.databse_password = ''
    args.category_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "main/data/category.json")
    return args

def check_construct_symbol(symbols):
    result = True
    rpm_name = 'libuninameslist-20180701-3.oe1.aarch64.rpm'
    so_name = 'libuninameslist.so.1.0.3'
    all_require_so = ['libc.so.6']
    out_symbol = ['_ITM_registerTMCloneTable', '__gmon_start__', '__cxa_finalize', '_ITM_deregisterTMCloneTable']
    u_symbol_table = []
    for symbol in symbols:
        if symbol.rpm_name != rpm_name or symbol.so_name != so_name or symbol.all_require_so != all_require_so:
            result = False
            break
        u_symbol_table.append(symbol.u_symbol_table)
    if u_symbol_table.sort() != out_symbol.sort():
        result = False
    return result


class TestRpmAnalyze(TestCase):
    def setUp(self):
        old_rpm_file_path = os.path.join(os.path.dirname(__file__), "data/old_rpms/")
        new_rpm_file_path = os.path.join(os.path.dirname(__file__), "data/new_rpms/")
        repository_old = Factory.create(old_rpm_file_path, fake_args(), "none")
        repository_new = Factory.create(new_rpm_file_path, fake_args(), "none")
        self.rpm_controller = RpmController(BRANCH_NAME, DB_PASSWORC)
        self.rpm_analyze = RpmAnalyze(fake_args(), repository_old=repository_old, repository_new=repository_new)

    def tearDown(self):
        # 清理环境
        self.rpm_controller.bulk_delete_datas(Symbol)
        self.rpm_controller.bulk_delete_datas(SymbolTemporary)
        self.rpm_controller.bulk_delete_datas(PullRequest)

    def test_collect_symbols(self):
        so_file = os.path.join(os.path.dirname(__file__), "data/")
        out_symbols = list(self.rpm_analyze.collect_symbols(so_file))
        correct_out_symbols = ['__gmon_start__', '_ITM_registerTMCloneTable',
                               '_ITM_deregisterTMCloneTable', '__cxa_finalize']
        self.assertEqual(correct_out_symbols.sort(), out_symbols.sort())

    def test_collect_required_so(self):
        binary_file = os.path.join(os.path.dirname(__file__), "data/libuninameslist.so.1.0.3")
        all_needed_so = self.rpm_analyze.collect_required_so(binary_file)
        correct_all_needed_so = ['libc.so.6']
        self.assertEqual(correct_all_needed_so, all_needed_so)

    def test_construct_symbol_structures(self):
        binary_files = [os.path.join(os.path.dirname(__file__), "data/libuninameslist.so.1.0.3")]
        rpm_name = 'libuninameslist-20180701-3.oe1.aarch64.rpm'
        self.rpm_analyze.construct_symbol_structures(self.rpm_controller, binary_files, rpm_name, Symbol)
        self.assertTrue(check_construct_symbol)

    def test_construct_database_symbol(self):
        self.assertEqual(getattr(self.rpm_analyze, "split_flag"), '__rpm__')
        is_tmp_table = False
        self.rpm_analyze.construct_database(is_tmp_table)
        query_symbol = RpmController(BRANCH_NAME, DB_PASSWORC).query_symbol_by_filter()
        self.assertTrue(query_symbol)

    def test_construct_database_symbol_tmp(self):
        is_tmp_table = True
        self.rpm_analyze.construct_database(is_tmp_table)
        query_symbol_tmp = self.rpm_controller.query_tmp_symbol()
        self.assertTrue(query_symbol_tmp)

        pr_mappings = self.rpm_controller.query_pr_mappings_by_pr_id(PR_ID)
        self.assertTrue(pr_mappings)

    def test_submit_symbol_change(self):
        self.rpm_analyze.construct_database(False)
        self.rpm_analyze.construct_database(True)
        self.rpm_analyze.submit_symbol_change()

        rpm_old_name = 'libuninameslist-20180701-3.oe1.aarch64.rpm'
        rpm_new_name = 'libuninameslist-new-3.oe1.aarch64.rpm'
        #提交之后symbol表为最新的数据
        query_symbol = self.rpm_controller.query_symbol_by_filter({'rpm_name': rpm_old_name})
        self.assertTrue(not query_symbol)

        query_symbol = self.rpm_controller.query_symbol_by_filter({'rpm_name': rpm_new_name})
        self.assertTrue(query_symbol)

        #提交之后symbol tmp表为空
        query_symbol_tmp = self.rpm_controller.query_tmp_symbol()
        self.assertTrue(not query_symbol_tmp)

        #提交之后pull request表为空
        query_pull_request = self.rpm_controller.query_pr_mappings_by_pr_id()
        self.assertTrue(not query_pull_request)


if __name__ == '__main__':
    main()
