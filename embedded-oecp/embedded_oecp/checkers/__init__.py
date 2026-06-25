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
from abc import ABC, abstractmethod
from typing import List
from embedded_oecp.models import TestResult


class BaseChecker(ABC):
    def __init__(self, config: dict, work_dir: str):
        self.config = config
        self.work_dir = work_dir

    @abstractmethod
    def run(self) -> List[TestResult]:
        pass

    def get_build_dir(self) -> str:
        return self.config.get("image_build", {}).get("dir", "")

    def get_source_dir(self) -> str:
        build_dir = self.get_build_dir()
        if build_dir:
            return os.path.normpath(os.path.join(build_dir, "..", "..", "src"))
        return ""
