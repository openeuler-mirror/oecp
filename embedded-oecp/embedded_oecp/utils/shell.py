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
import subprocess
import shlex
from typing import Tuple, Optional

from embedded_oecp.utils.logger import get_logger


def run_command(
    cmd,
    cwd: str = None,
    timeout: int = 600,
    env: dict = None,
) -> Tuple[str, str, int]:
    logger = get_logger()
    logger.debug(f"Running command: {cmd}")

    cmd_list = shlex.split(cmd) if isinstance(cmd, str) else cmd

    try:
        result = subprocess.run(
            cmd_list,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env or os.environ.copy(),
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout}s: {cmd}")
        return "", f"Command timed out after {timeout}s", -1
    except Exception as e:
        logger.error(f"Command execution error: {e}")
        return "", str(e), -1


def run_remote_command(
    host: str,
    user: str,
    password: Optional[str],
    command: str,
    **kwargs,
) -> Tuple[str, str, int]:
    logger = get_logger()
    timeout = kwargs.get("timeout", 300)
    port = kwargs.get("port", 22)
    logger.debug(f"Running remote command on {user}@{host}: {command}")

    result = _paramiko_command(host, user, password, command, timeout=timeout, port=port)
    if result is not None:
        return result

    ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10"]
    if password:
        ssh_cmd = ["sshpass", "-p", password] + ssh_cmd
    ssh_cmd.extend([f"{user}@{host}", "-p", str(port), command])

    try:
        proc = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=timeout)
        return proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired:
        return "", f"Remote command timed out after {timeout}s", -1
    except FileNotFoundError:
        ssh_fb = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
                  f"{user}@{host}", "-p", str(port), command]
        try:
            proc = subprocess.run(ssh_fb, capture_output=True, text=True, timeout=timeout)
            return proc.stdout, proc.stderr, proc.returncode
        except Exception as e:
            return "", str(e), -1
    except Exception as e:
        return "", str(e), -1


def _paramiko_command(host, user, password, command, **kwargs):
    logger = get_logger()
    timeout = kwargs.get("timeout", 300)
    port = kwargs.get("port", 22)
    ssh = None
    transport = None
    try:
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port=port, username=user, password=password or "", timeout=10)
        transport = ssh.get_transport()
        stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        rc = stdout.channel.recv_exit_status()
        for stream in (stdin, stdout, stderr):
            try:
                stream.close()
            except Exception as e:
                logger.debug(f"Stream close error: {e}")
        return out, err, rc
    except ImportError:
        return None
    except Exception:
        return None
    finally:
        if ssh is not None:
            try:
                ssh.close()
            except Exception as e:
                logger.debug(f"SSH close error: {e}")
        if transport is not None:
            try:
                transport.close()
            except Exception as e:
                logger.debug(f"Transport close error: {e}")
