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
from dataclasses import dataclass
from enum import Enum


class TestStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NONE = "NONE"
    RUNNING = "RUNNING"


class TestCategory(str, Enum):
    SOURCE = "源码"
    BUILD = "构建"
    RUNTIME = "运行时"
    SECURITY = "安全"


TEST_ITEMS = {
    "source": {
        "kernel": {"category": TestCategory.SOURCE, "sub_item": "内核", "display": "内核测试"},
        "middleware": {"category": TestCategory.SOURCE, "sub_item": "基础中间件", "display": "基础中间件（C库）测试"},
        "package": {"category": TestCategory.SOURCE, "sub_item": "其他软件包", "display": "其他软件包测试"},
    },
    "build": {
        "compiler": {"category": TestCategory.BUILD, "sub_item": "编译链", "display": "编译链检查"},
        "project": {"category": TestCategory.BUILD, "sub_item": "构建工程", "display": "构建工程检查"},
        "pkglist": {"category": TestCategory.BUILD, "sub_item": "包列表", "display": "包列表检查"},
    },
    "runtime": {
        "libc_runtime": {"category": TestCategory.RUNTIME, "sub_item": "C库运行时", "display": "C库运行时检查"},
        "at_test": {"category": TestCategory.RUNTIME, "sub_item": "基础功能", "display": "基础功能测试（AT）"},
        "posix": {"category": TestCategory.RUNTIME, "sub_item": "POSIX", "display": "POSIX测试"},
    },

}


@dataclass
class TestResult:
    category: str
    sub_item: str
    requirement: str
    acceptance_criteria: str
    status: str = TestStatus.NONE.value
    detail: str = ""
    evidence: str = ""
    remediation: str = ""

    def pass_test(self, detail: str = "", evidence: str = ""):
        self.status = TestStatus.PASS.value
        self.detail = detail
        self.evidence = evidence

    def fail_test(self, detail: str = "", evidence: str = "", remediation: str = ""):
        self.status = TestStatus.FAIL.value
        self.detail = detail
        self.evidence = evidence
        self.remediation = remediation

    def skip_test(self, detail: str = ""):
        self.status = TestStatus.NONE.value
        self.detail = detail

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "sub_item": self.sub_item,
            "requirement": self.requirement,
            "acceptance_criteria": self.acceptance_criteria,
            "status": self.status,
            "detail": self.detail,
            "evidence": self.evidence,
            "remediation": self.remediation,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TestResult":
        return cls(**data)

    def __str__(self):
        return f"[{self.status}] {self.category}/{self.sub_item}: {self.requirement}"
