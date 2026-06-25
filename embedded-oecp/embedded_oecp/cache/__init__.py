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
import json
from embedded_oecp.utils.logger import get_logger


class ResultCache:
    def __init__(self, work_dir: str):
        self.cache_dir = os.path.join(work_dir, "cache")
        os.makedirs(self.cache_dir, exist_ok=True)

    def _cache_path(self, test_name: str) -> str:
        return os.path.join(self.cache_dir, f"{test_name}.json")

    def save(self, test_name: str, results: list):
        logger = get_logger()
        path = self._cache_path(test_name)
        data = [r.to_dict() if hasattr(r, "to_dict") else r for r in results]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.debug(f"Cache saved: {path}")

    def load(self, test_name: str) -> list:
        path = self._cache_path(test_name)
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def load_all(self) -> dict:
        all_results = {}
        if os.path.isdir(self.cache_dir):
            for fname in os.listdir(self.cache_dir):
                if fname.endswith(".json"):
                    name = fname[:-5]
                    all_results[name] = self.load(name)
        return all_results

    def clear(self, test_names=None):
        if test_names:
            for name in test_names:
                path = self._cache_path(name)
                if os.path.isfile(path):
                    os.remove(path)
        else:
            if os.path.isdir(self.cache_dir):
                for f in os.listdir(self.cache_dir):
                    if f.endswith(".json"):
                        os.remove(os.path.join(self.cache_dir, f))

    def has_cache(self, test_name: str) -> bool:
        return os.path.isfile(self._cache_path(test_name))
