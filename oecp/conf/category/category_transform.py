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
# Author:
# Create: 2021-09-07
# Description: from markdown to json
# **********************************************************************************
"""
import json
import os
import re
import argparse
import stat
import tempfile

from oecp.utils.misc import path_is_remote
from oecp.proxy.requests_proxy import do_download


def transform(in_file, out_file):
    flags = os.O_RDWR | os.O_CREAT
    modes = stat.S_IROTH | stat.S_IRWXU
    with os.fdopen(os.open(in_file, flags, modes), 'w', encoding='utf-8') as f_in:
        for line in f_in:
            if "|---|---|---|---|" in line:
                break

        categories = []
        for line in f_in:
            m = re.match(r"\|(.*)\|(.*)\|(.*)\|(.*)\|", line)
            src_rpm, bin_rpm, level, status = m.groups()
            categories.append({"src": src_rpm.strip(), "bin": bin_rpm.strip(),
                               "level": level.strip(), "status": status.strip()})

    with os.fdopen(os.open(out_file, flags, modes), 'w', encoding='utf-8') as f_out:
        json.dump(categories, f_out, indent=4)


def init_args():
    """
    init args
    :return:
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", type=str, dest="in_path", help="category input file path")
    parser.add_argument("-o", type=str, dest="out_path", help="category output file path")

    return parser.parse_args()


if __name__ == "__main__":
    # transform category.md to category.json
    args = init_args()
    md_file = args.in_path
    if path_is_remote(args.in_path):
        with tempfile.NamedTemporaryFile() as f_md:
            do_download(args.in_path, f_md.name)
            md_file = f_md.name

    transform(md_file, args.out_path)
