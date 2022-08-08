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

from oecp.proxy.rpm_proxy import RPMProxy


def get_file_by_pattern(pattern, cache_dumper, kernel):
    kernel_name = RPMProxy.rpm_name(kernel)
    extract_path = cache_dumper.get_package_extract_path(kernel_name)
    if not extract_path:
        return
    for root, dirs, files in os.walk(extract_path):
        for item in files:
            if re.match(pattern, item):
                return os.path.join(root, item)
    return
