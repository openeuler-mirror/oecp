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
from embedded_oecp.utils.shell import run_command
from embedded_oecp.utils.logger import get_logger


def clone_or_pull(repo_url: str, target_dir: str, branch: str = None) -> bool:
    logger = get_logger()
    if os.path.isdir(os.path.join(target_dir, ".git")):
        logger.info(f"Repository exists, pulling: {target_dir}")
        stdout, stderr, rc = run_command("git pull", cwd=target_dir)
        if rc != 0:
            logger.warning(f"git pull failed: {stderr}")
        if branch:
            run_command(f"git checkout {branch}", cwd=target_dir)
        return True
    else:
        cmd = f"git clone {repo_url}"
        if branch:
            cmd += f" -b {branch}"
        cmd += f" {target_dir}"
        logger.info(f"Cloning: {cmd}")
        stdout, stderr, rc = run_command(cmd)
        if rc != 0:
            logger.error(f"git clone failed: {stderr}")
            return False
        return True


def get_commit_id(repo_dir: str, ref: str = "HEAD") -> str:
    stdout, stderr, rc = run_command(f'git log -1 --format="%H" {ref}', cwd=repo_dir)
    if rc == 0:
        return stdout.strip()
    return ""


def get_remote_url(repo_dir: str) -> str:
    for remote in ["origin", "upstream"]:
        stdout, stderr, rc = run_command(f"git remote get-url {remote}", cwd=repo_dir)
        if rc == 0 and stdout.strip():
            return stdout.strip()
    stdout, stderr, rc = run_command("git remote", cwd=repo_dir)
    if rc == 0 and stdout.strip():
        first_remote = stdout.strip().split("\n")[0].strip()
        stdout2, _, rc2 = run_command(f"git remote get-url {first_remote}", cwd=repo_dir)
        if rc2 == 0:
            return stdout2.strip()
    return ""
