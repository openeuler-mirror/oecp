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
import hashlib
import os
from typing import Optional
from embedded_oecp.utils.shell import run_command, run_remote_command
from embedded_oecp.utils.logger import get_logger


def compute_file_md5(filepath: str, chunk_size: int = 8192) -> Optional[str]:
    if not os.path.isfile(filepath):
        return None
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            md5.update(chunk)
    return md5.hexdigest()


def remote_md5sum(host: str, user: str, password: str, filepath: str, port: int = 22) -> Optional[str]:
    stdout, stderr, rc = run_remote_command(host, user, password, f"md5sum {filepath}", port=port)
    if rc == 0 and stdout.strip():
        return stdout.strip().split()[0]
    return None


def remote_find_and_md5(host: str, user: str, password: str, filename: str, port: int = 22) -> Optional[str]:
    cmd = f'find /usr/lib* /lib* -name "{filename}" -type f 2>/dev/null | head -1'
    stdout, stderr, rc = run_remote_command(host, user, password, cmd, port=port)
    if rc == 0 and stdout.strip():
        filepath = stdout.strip().split("\n")[0]
        return remote_md5sum(host, user, password, filepath, port=port)
    return None
