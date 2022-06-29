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
import re
import os


def path_is_remote(path):
    """
    远程地址
    :param path:
    :return:
    """
    try:
        return not not re.match("^(ftp|https?)://.+", path, re.IGNORECASE)
    except:
        return False


def basename_of_path(path):
    """
    获取path的basename，支持URL格式
    :param path:
    :return:
    """
    return os.path.basename(path.rstrip("/"))
