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
from oecp.db.symbol import Symbol
from oecp.db.symbol_temporary import SymbolTemporary
from oecp.db.pull_request import PullRequest
from oecp.symbol_analyze.db_api import Api

SYMBOLS_LIST = [
    {
        'rpm_name': 'folks-0.11.4-10.oe1.aarch64.rpm',
        'so_name': 'libfolks.so.25.18.4',
        'u_symbol_table': 'g_utf8_normalize',
        'association_so_name': '["libgio-2.0.so.0", "libgmodule-2.0.so.0", "libgee-0.8.so.2", "libgobject-2.0.so.0"}]'
    },
    {
        'rpm_name': 'vala-0.42.2-2.oe1.aarch64.rpm',
        'so_name': 'libvalaccodegen.so',
        'u_symbol_table': 'vala_method_get_async_end_parameters',
        'association_so_name': '["libvala-0.42.so.0", "libgmodule-2.0.so.0", "libgobject-2.0.so.0", "libglib-2.0.so.0"]'
    },
    {
        'rpm_name': 'vino-3.22.0-12.oe1.aarch64.rpm',
        'so_name': 'vino-server',
        'u_symbol_table': 'g_hash_table_iter_next',
        'association_so_name': '["libgtk-3.so.0", "libgdk-3.so.0", "libpangocairo-1.0.so.0", "libpango-1.0.so.0"]'
    }
]

PULLREQUEST = {
    'pr_id': '123456',
    'rpm_name': 'folks-0.11.4-10.oe1.aarch64.rpm',
    'is_rpm_new': True
}

def check_symbol_equal(symbols, correct_data):
    symbol_list = []
    for symbol in symbols:
        symbol_list.append(dict(rpm_name=symbol.rpm_name, so_name=symbol.so_name,
                                u_symbol_table=symbol.u_symbol_table,
                                association_so_name=symbol.association_so_name))
    result = True if symbol_list == correct_data else False
    return result


class TestApi(TestCase):
    def setUp(self):
        self.db = Api(database_name='unit_test', db_password='')

    def tearDown(self):
        self.db.delete_by_rpm_name(Symbol)
        self.db.delete_by_rpm_name(SymbolTemporary)
        self.db.delete_pr_mapping_by_pr_id('123456')

    def test_get_session(self):
        self.assertTrue(self.db.session)

    def test_bulk_save_objects_and_query(self):
        symbol_models = []
        symbol_tmp_models = []
        for symbol in SYMBOLS_LIST:
            symbol_models.append(Symbol(rpm_name=symbol['rpm_name'], so_name=symbol['so_name'],
                       u_symbol_table=symbol['u_symbol_table'], association_so_name=symbol['association_so_name']))
            symbol_tmp_models.append(SymbolTemporary(rpm_name=symbol['rpm_name'], so_name=symbol['so_name'],
                       u_symbol_table=symbol['u_symbol_table'], association_so_name=symbol['association_so_name']))
        self.db.bulk_save_objects(symbol_models)
        query_symbols = self.db.query_symbol()
        self.assertTrue(check_symbol_equal(query_symbols, SYMBOLS_LIST))

        self.db.bulk_save_objects(symbol_tmp_models)
        query_tmp_symbols = self.db.query_symbol_tmp()
        self.assertTrue(check_symbol_equal(query_tmp_symbols, SYMBOLS_LIST))

        self.db.bulk_save_objects([PullRequest(pr_id=PULLREQUEST['pr_id'], rpm_name=PULLREQUEST['rpm_name'],
                                               is_rpm_new=PULLREQUEST['is_rpm_new'])])
        query_pull_request = self.db.query_pr_mappings_by_pr_id(pr_id='123456')
        self.assertEqual({'pr_id': query_pull_request[0].pr_id, 'rpm_name': query_pull_request[0].rpm_name,
                          'is_rpm_new': query_pull_request[0].is_rpm_new}, PULLREQUEST)

    def test_select_symbol_contains_so(self):
        symbol_models = []
        for symbol in SYMBOLS_LIST:
            symbol_models.append(Symbol(rpm_name=symbol['rpm_name'], so_name=symbol['so_name'],
                       u_symbol_table=symbol['u_symbol_table'], association_so_name=symbol['association_so_name']))
        self.db.bulk_save_objects(symbol_models)
        query_filter = {'u_symbol_table': 'g_hash_table_iter_next', 'association_so_name': 'libpango-1.0.so.0'}
        query_symbol = self.db.select_symbol_contains_so(query_filter)
        correct_symbol = [{
            'rpm_name': 'vino-3.22.0-12.oe1.aarch64.rpm',
            'so_name': 'vino-server',
            'u_symbol_table': 'g_hash_table_iter_next',
            'association_so_name': '["libgtk-3.so.0", "libgdk-3.so.0", "libpangocairo-1.0.so.0", "libpango-1.0.so.0"]'}]
        self.assertTrue(check_symbol_equal(query_symbol, correct_symbol))

    def test_delete_by_rpm_name(self):
        symbol_models = []
        symbol_tmp_models = []
        for symbol in SYMBOLS_LIST:
            symbol_models.append(Symbol(rpm_name=symbol['rpm_name'], so_name=symbol['so_name'],
                                        u_symbol_table=symbol['u_symbol_table'],
                                        association_so_name=symbol['association_so_name']))
            symbol_tmp_models.append(SymbolTemporary(rpm_name=symbol['rpm_name'], so_name=symbol['so_name'],
                                                     u_symbol_table=symbol['u_symbol_table'],
                                                     association_so_name=symbol['association_so_name']))
        self.db.bulk_save_objects(symbol_models)
        self.db.bulk_save_objects(symbol_tmp_models)

        query_filter = {'rpm_name': 'folks-0.11.4-10.oe1.aarch64.rpm'}
        self.db.delete_by_rpm_name(Symbol, 'folks-0.11.4-10.oe1.aarch64.rpm')
        symbol_folks = self.db.query_symbol(query_filter)
        self.assertEqual(symbol_folks, [])

        self.db.delete_by_rpm_name(SymbolTemporary, 'folks-0.11.4-10.oe1.aarch64.rpm')
        symbol_tmp_folks = self.db.query_symbol_tmp(query_filter)
        self.assertEqual(symbol_tmp_folks, [])

    def test_delete_pr_mapping_by_pr_id(self):
        self.db.bulk_save_objects([PullRequest(pr_id=PULLREQUEST['pr_id'], rpm_name=PULLREQUEST['rpm_name'],
                                               is_rpm_new=PULLREQUEST['is_rpm_new'])])
        self.db.delete_pr_mapping_by_pr_id('123456')
        query_pull_request = self.db.query_pr_mappings_by_pr_id(pr_id='123456')
        self.assertEqual(query_pull_request, [])

if __name__ == '__main__':
    main()