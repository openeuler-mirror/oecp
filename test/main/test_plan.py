# -*- encoding=utf-8 -*-
"""
# **********************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# [oecp] is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author:
# Create: 2021-09-07
# Description: test compare plan
# **********************************************************************************
"""
import os
import logging
from unittest import TestCase

from oecp.main.plan import Plan
from oecp.utils.logger import init_logger


class TestPlan(TestCase):
    @classmethod
    def setUpClass(cls):
        init_logger()
        cls.logger = logging.getLogger("test")

    def test_construct(self):
        plan_file = os.path.join(os.path.dirname(__file__), "data/plan.json")
        plan = Plan(plan_file)
        self.assertEqual(getattr(plan, "_plan_name"), "test")

    def test_plan_file_not_found(self):
        plan_file = os.path.join(os.path.dirname(__file__), "data_not_found")

        with self.assertRaises(FileNotFoundError):
            Plan(plan_file)

    def test_is_direct(self):
        plan_file = os.path.join(os.path.dirname(__file__), "data/plan.json")
        plan = Plan(plan_file)
        self.assertEqual(plan.is_direct("provides"), False)

    def test_dumper(self):
        plan_file = os.path.join(os.path.dirname(__file__), "data/plan.json")
        plan = Plan(plan_file)

        dumper = plan.dumper_of("provides")
        self.assertEqual(dumper.__name__, "ProvidesDumper")
        dumper = plan.dumper_of("requires")
        self.assertEqual(dumper.__name__, "RequiresDumper")

    def test_dumper_not_exist(self):
        plan_file = os.path.join(os.path.dirname(__file__), "data/plan.json")
        plan = Plan(plan_file)

        with self.assertRaises(KeyError):
            dumper = plan.dumper_of("not_exist")

    def test_executor(self):
        plan_file = os.path.join(os.path.dirname(__file__), "data/plan.json")
        plan = Plan(plan_file)

        executor = plan.executor_of("provides")
        self.assertEqual(executor.__name__, "NVSCompareExecutor")

        executor = plan.executor_of("requires")
        self.assertEqual(executor.__name__, "NVSCompareExecutor")

    def test_config(self):
        plan_file = os.path.join(os.path.dirname(__file__), "data/plan.json")
        plan = Plan(plan_file)

        config = plan.config_of("provides")
        self.assertEqual(config, {'compare_type': 'rpm provides'})

        config = plan.config_of("requires")
        self.assertEqual(config, {'compare_type': 'rpm requires'})
