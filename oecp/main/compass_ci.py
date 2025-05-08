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
# Create: 2021-09-06
# Description: compare plan
# **********************************************************************************
"""
import logging
from oecp.compass_ci.connect_compass_ci import ConnectCompassCI


logger = logging.getLogger("oecp")

def init_compass_ci(iso_path, job_type='at'):
    connector = ConnectCompassCI(iso_path=iso_path, job_type=job_type)
    return connector


def submit(connector):
    job_id = connector.submit()
    return job_id


def get_results(connector):
    res = connector.get_results()
    return res


def release_compas_ci(connector):
    del connector


def submit_compass_ci_job_get_result(iso_path, job_type='at'):
    connector = init_compass_ci(iso_path, job_type)
    for i in range(5):
        submit(connector)
        res = get_results(connector)
        if res:
            return res
    return None


def _main():
    import os
    def is_aarch64(iso_name):
        if "aarch64" in iso_name:
            return True
        if "arm64" in iso_name:
            return True
        return False
    
    def is_x86(iso_name):
        if "x86_64" in iso_name:
            return True
        if "x86" in iso_name:
            return True
        if "amd64" in iso_name:
            return True
        return False

    iso_path = '/root/wangkui/datasource/Kylin-Server-10-SP1-aarch64-Release-Build04-20200711.iso'
    # iso_path = '/root/wangkui/datasource/KylinSec-Server-3.4-4A-2108-132155-x86_64.iso'
    iso_path = '/root/wangkui/datasource'
    iso_name = """
eulixos:aarch64:1.0               EulixOS-Server-1.0-aarch64.iso
"""
    for name in iso_name.split('\n'):
        name = name.strip()
        if not name:
            continue
        if name[0] == '#':
            continue
        info, iso = name.split()
        # if not is_aarch64(iso):
        #     continue
        print(iso)
        res = submit_compass_ci_job_get_result(os.path.join(iso_path, iso), job_type='at')
        print(res)


if __name__ == "__main__":
    _main()
    