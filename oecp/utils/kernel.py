# -*- encoding=utf-8 -*-
"""
# **********************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# [oecp] is licensed under the Mulan PSL v1.
# You can use this software according to the terms and conditions of the Mulan PSL v1.
# You may obtain a copy of Mulan PSL v1 at:
#     http://license.coscl.org.cn/MulanPSL
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v1 for more details.
# **********************************************************************************
"""

import os
import re


def get_file_by_pattern(pattern, cache_dumper):
    query_file = ""
    extract_paths = cache_dumper.get_package_extract_path()

    for extract_path in extract_paths:
        if not extract_path:
            continue
        for root, dirs, files in os.walk(extract_path):
            for item in files:
                if re.match(pattern, item):
                    query_file = os.path.join(root, item)
                    break
        if query_file:
            break

    return query_file
