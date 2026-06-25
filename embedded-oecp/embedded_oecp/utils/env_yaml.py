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
import re
import yaml
from embedded_oecp.utils.logger import get_logger


def build_env_yaml_url(baseline_repo: str, baseline_branch: str) -> str:
    m = re.match(r'https?://[^/]+/([^/]+/[^/]+?)(?:\.git)?$', baseline_repo)
    if not m:
        return ""
    repo_path = m.group(1)
    return f"https://raw.atomgit.com/{repo_path}/raw/{baseline_branch}/.oebuild/env.yaml"


def load_env_yaml(work_dir: str, baseline_repo: str = None, baseline_branch: str = None) -> dict:
    logger = get_logger()

    if baseline_repo and baseline_branch:
        url = build_env_yaml_url(baseline_repo, baseline_branch)
        if url:
            data = _fetch_remote_yaml(url)
            if data:
                return data

    env_path = _find_env_yaml(work_dir)
    if env_path:
        logger.info(f"Loading env.yaml from {env_path}")
        with open(env_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def _fetch_remote_yaml(url: str) -> dict:
    logger = get_logger()
    logger.info(f"Fetching env.yaml from {url}")
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "embedded-oecp/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode("utf-8")
        data = yaml.safe_load(content) or {}
        logger.info(f"Successfully loaded remote env.yaml ({len(content)} bytes)")
        return data
    except Exception as e:
        logger.warning(f"Failed to fetch remote env.yaml: {e}")
        return {}


def _find_env_yaml(work_dir: str) -> str:
    candidates = [
        os.path.join(work_dir, "env.yaml"),
        os.path.join(work_dir, ".oebuild", "env.yaml"),
        os.path.join(work_dir, "yocto-meta-openeuler", ".oebuild", "env.yaml"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return ""


def get_arch_baseline(env_data: dict, arch: str) -> dict:
    return env_data.get(arch, {})


def get_toolchain_md5(env_data: dict, arch: str) -> dict:
    arch_data = get_arch_baseline(env_data, arch)
    return arch_data.get("toolchain_md5", {})


def get_runtime_md5(env_data: dict, arch: str) -> dict:
    arch_data = get_arch_baseline(env_data, arch)
    return arch_data.get("runtime_md5", {})


def get_glibc_md5(env_data: dict, arch: str) -> str:
    legacy_keys = {
        "aarch64": "aarch64_glibc_md5",
        "arm32": "arm32_glibc_md5",
        "x86_64": "x86_64_glibc_md5",
        "riscv64": "riscv64_glibc_md5",
    }
    key = legacy_keys.get(arch)
    if key and key in env_data:
        return env_data[key]
    runtime = get_runtime_md5(env_data, arch)
    libc = runtime.get("libc_so", {})
    if isinstance(libc, dict):
        return libc.get("md5", "")
    return ""
