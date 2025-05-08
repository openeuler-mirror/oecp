# -*- encoding=utf-8 -*-
"""
# **********************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2021-2021. All rights reserved.
# [oecp] is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author:
# Create: 2022-04-06
# Description: File compress
# **********************************************************************************
"""

import hashlib
import logging
import os
import time
import tarfile

logger = logging.getLogger("oecp")

def filter_general(item):
    """
    filter func
    item: tarinfo

    Returns:
    """
    if "tar.gz" in item.name:
        return None
    return item

def gen_hash_key(file):
    """
    Args:
        file: file that need to be computed by hash values
    """
    try:
        hash_obj = hashlib.md5()
        with open(file, 'rb') as a_file:
            hash_obj.update(a_file.read())
    except (PermissionError, IsADirectoryError, FileNotFoundError) as err:
        return
    else:
        return hash_obj.hexdigest()

def compress_report(osv_title, output_path):
    """
    Description: Compress the final report file

    Args:
        osv_title: Report name
        output_path: Compressed file storage path

    Returns:
    """
    timestamp = time.strftime("%Y%m%d%H%M%S", time.localtime())
    report_dir = os.path.join(output_path, osv_title)
    if os.path.exists(report_dir):
        with tarfile.open(f"{output_path}/report{timestamp}.tar.gz", "w:gz") as tar:
            tar.add(report_dir, arcname=osv_title, filter=filter_general)
    else:
        logger.warning(f"report {report_dir} lost.")