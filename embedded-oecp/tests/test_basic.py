# **********************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2026-2026. All rights reserved.
# [embedded-oecp] is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author: lixinyu
# Create: 2025-01-01
# Description: embedded-oecp utility
# **********************************************************************************
import unittest
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embedded_oecp.models import TestResult


class TestTestResult(unittest.TestCase):
    def test_pass_test(self):
        r = TestResult(category="源码", sub_item="内核", requirement="test", acceptance_criteria="test")
        r.pass_test(detail="all good", evidence="evidence.txt")
        self.assertEqual(r.status, "PASS")
        self.assertEqual(r.detail, "all good")

    def test_fail_test(self):
        r = TestResult(category="源码", sub_item="内核", requirement="test", acceptance_criteria="test")
        r.fail_test(detail="something wrong", remediation="fix it")
        self.assertEqual(r.status, "FAIL")
        self.assertEqual(r.remediation, "fix it")

    def test_skip_test(self):
        r = TestResult(category="源码", sub_item="内核", requirement="test", acceptance_criteria="test")
        r.skip_test(detail="not applicable")
        self.assertEqual(r.status, "SKIP")

    def test_str_representation(self):
        r = TestResult(category="源码", sub_item="内核", requirement="test", acceptance_criteria="test")
        r.pass_test()
        self.assertIn("PASS", str(r))
        self.assertIn("源码", str(r))


class TestConfig(unittest.TestCase):
    def test_load_default_config(self):
        from embedded_oecp.utils.config import load_config
        config = load_config(None)
        self.assertIn("source", config)
        self.assertIn("device", config)
        self.assertIn("oebuild", config)

    def test_deep_merge(self):
        from embedded_oecp.utils.config import _deep_merge
        base = {"a": {"b": 1, "c": 2}, "d": 3}
        override = {"a": {"b": 10}, "e": 5}
        result = _deep_merge(base, override)
        self.assertEqual(result["a"]["b"], 10)
        self.assertEqual(result["a"]["c"], 2)
        self.assertEqual(result["d"], 3)
        self.assertEqual(result["e"], 5)


class TestReportGenerator(unittest.TestCase):
    def test_generate_report(self):
        from embedded_oecp.report.generator import ReportGenerator
        import tempfile

        results = [
            TestResult(category="源码", sub_item="内核", requirement="test1", acceptance_criteria="ac1"),
            TestResult(category="源码", sub_item="中间件", requirement="test2", acceptance_criteria="ac2"),
        ]
        results[0].pass_test(detail="ok")
        results[1].fail_test(detail="bad", remediation="fix")

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = ReportGenerator(output_dir=tmpdir)
            gen.generate(results)

            self.assertTrue(os.path.exists(os.path.join(tmpdir, "report.json")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "report.md")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "summary.txt")))


class TestRunnerPlanMap(unittest.TestCase):
    def test_plan_map_keys(self):
        from embedded_oecp.runner import PLAN_MAP
        self.assertIn("all", PLAN_MAP)
        self.assertIn("source", PLAN_MAP)
        self.assertIn("build", PLAN_MAP)
        self.assertIn("runtime", PLAN_MAP)

    def test_all_plan_contains_all_checkers(self):
        from embedded_oecp.runner import PLAN_MAP
        all_checkers = PLAN_MAP["all"]
        self.assertIn("kernel", all_checkers)
        self.assertIn("middleware", all_checkers)
        self.assertIn("package", all_checkers)
        self.assertIn("compiler", all_checkers)
        self.assertIn("project", all_checkers)
        self.assertIn("pkglist", all_checkers)
        self.assertIn("middleware_runtime", all_checkers)
        self.assertIn("at_test", all_checkers)
        self.assertIn("posix", all_checkers)


if __name__ == "__main__":
    unittest.main()
