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
# Create: 2021-11-22
# Description: get drive kabi whitelist
# **********************************************************************************
"""


"""
how to use:
    python3 drive_kabi.py $drive_list_file $drive_kabi_file
example:
    python3 drive_kabi.py ../conf/kernel_driver_range/drives.json ../conf/kabi_whitelist/aarch64_drive_kabi
"""
import os
import sys
import json
import time
import subprocess

def shell_cmd(cmd):
    p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()

    return p.returncode, out.decode("utf-8", errors="ignore"), err.decode("utf-8", errors="ignore")

def get_drive_kabi():
    ko_kabi = get_ko_kabi()
    base_kabi = get_base_kabi()
    lost_kabi, kind_kabi, drive_kabi = get_kabi_statistic(ko_kabi, base_kabi)
    create_drive_kabi(drive_kabi)
    create_lost_kabi(lost_kabi)
    create_kind_kabi(kind_kabi)

def get_modules_kernel():
    c, o, e = shell_cmd("uname -a | awk '{print $3}'")
    return "/usr/lib/modules/%s/kernel" % (o.strip())

def get_drives():
    with open(sys.argv[1]) as fp:
        drives = json.load(fp)
    return drives

def get_ko_kabi():
    ko_kabi = {}
    drives = get_drives()
    kernel = get_modules_kernel()
    for drive in drives:
        c, o, e = shell_cmd("find %s -name %s.ko" % (kernel, drive))
        if o.strip() != '':
            c, o, e = shell_cmd("nm -u %s | awk '{print $2}'" % (o.strip()))
            ko_kabi[drive] = o.strip()

    return ko_kabi

def get_base_kabi():
    base_kabi = []

    with open(sys.argv[2]) as fp:
        line = fp.readline()
        while line:
            base_kabi.append(line.strip())
            line = fp.readline()

    return base_kabi

def get_kabi_statistic(ko_kabi, base_kabi):
    lost_kabi = {}
    kind_kabi = {}
    drive_kabi = []
    bl = base_kabi
    
    for k, v in ko_kabi.items():
        vl = v.split()
        cl = list(set(bl).intersection(set(vl)))
        drive_kabi += cl
        kind_kabi[k] = cl
        t = list(set(vl).difference(set(cl)))
        if len(t) != 0:
            lost_kabi[k] = t
    drive_kabi = list(set(drive_kabi))
    print(kind_kabi)

    return lost_kabi, kind_kabi, sorted(drive_kabi)

def create_drive_kabi(drive_kabi):
    dkj = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'drive_kabi')

    with open(dkj, 'w') as fp:
        for line in drive_kabi:
            fp.write(line + '\n')

def create_lost_kabi(lost_kabi):
    lkj = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lost_kabi')

    with open(lkj, 'w', encoding='utf-8') as fp:
        json.dump(lost_kabi, fp, indent=2, sort_keys=True, ensure_ascii=False)

def create_kind_kabi(kind_kabi):
    kkj = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kind_kabi')

    with open(kkj, 'w') as fp:
        json.dump(kind_kabi, fp, indent=2, sort_keys=True, ensure_ascii=False)

if __name__ == '__main__':
    get_drive_kabi()
