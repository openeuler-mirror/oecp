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

import os
import re

def get_file_by_pattern(pattern, cache_dumper):
    extract_paths = []
    extract_paths.append(cache_dumper.get_package_extract_path('kernel'))
    extract_paths.append(cache_dumper.get_package_extract_path('kernel-core'))

    for extract_path in extract_paths:
        if not extract_path:
            continue
        for root, dirs, files in os.walk(extract_path):
            for item in files:
                if re.match(pattern, item):
                    return os.path.join(root, item)
