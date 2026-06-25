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
import os
from typing import List, Optional
from embedded_oecp.models import TestResult, TEST_ITEMS, TestStatus
from embedded_oecp.cache import ResultCache
from embedded_oecp.utils.logger import get_logger

from embedded_oecp.checkers.source.kernel_checker import KernelChecker
from embedded_oecp.checkers.source.middleware_checker import MiddlewareChecker
from embedded_oecp.checkers.source.package_checker import PackageChecker
from embedded_oecp.checkers.build.compiler_checker import CompilerChecker
from embedded_oecp.checkers.build.project_checker import ProjectChecker
from embedded_oecp.checkers.build.pkglist_checker import PkgListChecker
from embedded_oecp.checkers.runtime.middleware_runtime_checker import MiddlewareRuntimeChecker
from embedded_oecp.checkers.runtime.at_test_checker import ATTestChecker
from embedded_oecp.checkers.runtime.posix_checker import PosixChecker

CHECKER_MAP = {
    "kernel": KernelChecker,
    "middleware": MiddlewareChecker,
    "package": PackageChecker,
    "compiler": CompilerChecker,
    "project": ProjectChecker,
    "pkglist": PkgListChecker,
    "libc_runtime": MiddlewareRuntimeChecker,
    "at_test": ATTestChecker,
    "posix": PosixChecker,

}


def resolve_checkers(plan: str) -> List[str]:
    if plan in TEST_ITEMS:
        return list(TEST_ITEMS[plan].keys())
    all_names = []
    for group in TEST_ITEMS.values():
        all_names.extend(group.keys())
    if plan in all_names:
        return [plan]
    if plan == "all":
        return all_names
    raise ValueError(f"Unknown plan: {plan}. Available: all, {', '.join(TEST_ITEMS.keys())}, or specific test name")


class TestRunner:
    def __init__(self, config: dict):
        self.config = config
        self.work_dir = config.get("work_dir", "/tmp/embedded-oecp")
        self.cache = ResultCache(self.work_dir)
        self.logger = get_logger()

    def _create_checker(self, name: str):
        cls = CHECKER_MAP.get(name)
        if cls is None:
            raise ValueError(f"Unknown checker: {name}")
        return cls(config=self.config, work_dir=self.work_dir)

    def run(self, plan: str = "all", force: bool = False) -> List[TestResult]:
        checker_names = resolve_checkers(plan)
        all_results = []

        for name in checker_names:
            if not force and self.cache.has_cache(name):
                self.logger.info(f"=== Using cached results: {name} ===")
                cached = self.cache.load(name)
                for item in cached:
                    all_results.append(TestResult.from_dict(item))
                continue

            self.logger.info(f"=== Running checker: {name} ===")
            try:
                checker = self._create_checker(name)
                results = checker.run()
                self.cache.save(name, results)
                all_results.extend(results)
            except Exception as e:
                self.logger.error(f"Checker {name} failed: {e}")
                result = TestResult(
                    category=name, sub_item="error",
                    requirement="Checker execution", acceptance_criteria="No exception",
                    status=TestStatus.FAIL.value, detail=str(e),
                )
                self.cache.save(name, [result.to_dict()])
                all_results.append(result)

        return all_results

    def summary(self) -> List[TestResult]:
        all_cached = self.cache.load_all()
        summary_rows = []

        for group_name, items in TEST_ITEMS.items():
            for item_name, meta in items.items():
                cached = all_cached.get(item_name, [])
                if cached:
                    worst = TestStatus.NONE.value
                    for r in cached:
                        s = r.get("status", TestStatus.NONE.value)
                        if s == TestStatus.FAIL.value:
                            worst = TestStatus.FAIL.value
                            break
                        elif s == TestStatus.PASS.value:
                            worst = TestStatus.PASS.value
                    status = worst
                    detail = "; ".join(r.get("detail", "") for r in cached if r.get("detail"))
                else:
                    status = TestStatus.NONE.value
                    detail = "未测试"

                summary_rows.append(TestResult(
                    category=meta["category"].value,
                    sub_item=meta["sub_item"],
                    requirement=meta["display"],
                    acceptance_criteria="",
                    status=status,
                    detail=detail,
                ))

        return summary_rows

    def conclusion(self) -> str:
        results = self.summary()
        statuses = [r.status for r in results]
        if any(s == TestStatus.FAIL.value for s in statuses):
            return "不通过"
        if any(s == TestStatus.NONE.value for s in statuses):
            return "待整改"
        if all(s == TestStatus.PASS.value for s in statuses):
            return "通过"
        return "待整改"
