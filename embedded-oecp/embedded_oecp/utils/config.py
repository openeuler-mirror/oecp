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
import yaml
from embedded_oecp.utils.logger import get_logger

_DEFAULT_CONFIG = {
    "baseline_repo": "https://atomgit.com/alichinese_admin/yocto-meta-openeuler.git",
    "baseline_branch": "env",
    "work_dir": None,
    "output_dir": None,
    "verbose": False,
    "arch": None,
    "kernel": {"mainstream_versions": ["5.10", "6.6"]},
    "image_build": {"dir": None},
    "toolchain": {"dir": None},
    "device": {"ip": None, "user": "root", "password": None, "port": 22},
    "mugen": {
        "dir": None,
        "at_config": "embedded_at_test.json",
        "posix_config": "embedded_posix_test.json",
        "posix_baseline": None,
    },
}


def get_default_workdir() -> str:
    _package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _project_root = os.path.dirname(_package_dir)
    return os.path.join(_project_root, "workdir")


def ensure_workdir(workdir: str = None) -> str:
    if workdir is None:
        workdir = get_default_workdir()
    os.makedirs(workdir, exist_ok=True)
    os.makedirs(os.path.join(workdir, "conf"), exist_ok=True)
    os.makedirs(os.path.join(workdir, "cache"), exist_ok=True)
    os.makedirs(os.path.join(workdir, "report", "evidence"), exist_ok=True)

    conf_path = os.path.join(workdir, "conf", "config.yaml")
    if not os.path.isfile(conf_path):
        pkg_default = os.path.join(os.path.dirname(__file__), "..", "default_config.yaml")
        if os.path.isfile(pkg_default):
            import shutil
            shutil.copy2(pkg_default, conf_path)

    return workdir


def load_config(config_path: str = None, workspace: str = None) -> dict:
    logger = get_logger()
    if workspace is None:
        workspace = get_default_workdir()

    config = {}
    for k, v in _DEFAULT_CONFIG.items():
        config[k] = v.copy() if isinstance(v, dict) else v

    resolved_conf = ""
    if config_path:
        resolved_conf = config_path
    elif workspace:
        resolved_conf = os.path.join(workspace, "conf", "config.yaml")

    if resolved_conf and os.path.isfile(resolved_conf):
        logger.info(f"Loading config from {resolved_conf}")
        with open(resolved_conf, "r", encoding="utf-8") as f:
            user_config = yaml.safe_load(f) or {}
        config = _deep_merge(config, user_config)
    else:
        logger.info("No config file found, using defaults")

    config["work_dir"] = workspace
    if not config.get("output_dir"):
        config["output_dir"] = os.path.join(workspace, "report")

    if config.get("work_dir"):
        os.makedirs(config["work_dir"], exist_ok=True)
    if config.get("output_dir"):
        os.makedirs(config["output_dir"], exist_ok=True)
    return config


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
