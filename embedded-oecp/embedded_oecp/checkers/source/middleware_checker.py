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
from typing import List
from embedded_oecp.checkers import BaseChecker
from embedded_oecp.models import TestResult
from embedded_oecp.utils.env_yaml import load_env_yaml, get_runtime_md5, build_env_yaml_url
from embedded_oecp.utils.shell import run_remote_command
from embedded_oecp.utils.logger import get_logger
from embedded_oecp.utils.terminal_screenshot import render_terminal_screenshot


class MiddlewareChecker(BaseChecker):
    def __init__(self, config: dict, work_dir: str):
        super().__init__(config, work_dir)
        self._evidence_dir = ""
        self._env_data = None
        self._env_url = ""
        self._device_md5 = None
        self._device_path = None

    def run(self) -> List[TestResult]:
        self._evidence_dir = os.path.join(
            self.config.get("output_dir", "/tmp/embedded-oecp/report"), "evidence",
        )
        os.makedirs(self._evidence_dir, exist_ok=True)

        baseline_repo = self.config.get("baseline_repo", "")
        baseline_branch = self.config.get("baseline_branch", "")
        self._env_url = build_env_yaml_url(baseline_repo, baseline_branch)
        self._env_data = load_env_yaml(self.work_dir, baseline_repo, baseline_branch)

        results = []
        results.append(self._step1_device_md5())
        results.append(self._step2_baseline())
        results.append(self._step3_compare())
        return results

    def _get_device_config(self):
        device_cfg = self.config.get("device", {})
        return (
            device_cfg.get("ip", ""),
            device_cfg.get("user", "root"),
            device_cfg.get("password", ""),
            device_cfg.get("port", 22),
        )

    def _get_libc_info(self):
        arch = self.config.get("arch")
        runtime_md5 = get_runtime_md5(self._env_data, arch)
        return runtime_md5.get("libc_so", {}) if isinstance(runtime_md5, dict) else {}

    def _step1_device_md5(self) -> TestResult:
        result = TestResult(
            category="源码", sub_item="基础中间件",
            requirement="从目标设备提取 libc.so 的 MD5 值",
            acceptance_criteria="成功执行 md5sum /usr/lib*/libc.so* 并获取 MD5",
        )

        host, user, password, port = self._get_device_config()
        if not host:
            result.fail_test(
                detail="未配置目标设备 IP",
                remediation="请使用 --device-ip 或配置 device.ip",
            )
            return result

        stdout, stderr, rc = run_remote_command(
            host, user, password,
            "md5sum /usr/lib*/libc.so* /lib*/libc.so* 2>/dev/null",
            port=port,
        )

        lines = [
            {"text": f"# 目标设备: {user}@{host}", "color": "#6c7086"},
            {"text": "", "color": "#cdd6f4"},
            {"text": f"$ ssh {user}@{host} 'md5sum /usr/lib*/libc.so* /lib*/libc.so*'", "type": "command"},
        ]

        if stdout and stdout.strip():
            output_lines = stdout.strip().split("\n")
            for ol in output_lines:
                lines.append({"text": ol, "color": "#f9e2af", "type": "highlight"})

            parts = output_lines[0].split(None, 1)
            self._device_md5 = parts[0] if parts else None
            self._device_path = parts[1].strip() if len(parts) > 1 else None

            lines.append({"text": "", "color": "#cdd6f4"})
            lines.append({"text": f"成功提取 libc.so MD5: {self._device_md5}", "type": "success"})
        else:
            self._device_md5 = None
            self._device_path = None
            err_msg = stderr.strip() if stderr else "未找到 libc.so"
            lines.append({"text": err_msg, "color": "#f38ba8"})
            lines.append({"text": "", "color": "#cdd6f4"})
            lines.append({"text": "未找到 libc.so", "type": "error"})

        path = os.path.join(self._evidence_dir, "middleware_step1_device_md5.png")
        render_terminal_screenshot("Step 1: 目标设备 libc.so MD5 提取", lines, path)

        if self._device_md5:
            result.pass_test(
                detail=f"libc.so({self._device_path})的MD5为{self._device_md5}",
                evidence=f"screenshot: {path}",
            )
        else:
            result.fail_test(
                detail="目标设备上未找到 libc.so",
                evidence=f"screenshot: {path}",
                remediation="请检查目标设备上 /usr/lib* 下是否存在 libc.so",
            )
        return result

    def _step2_baseline(self) -> TestResult:
        result = TestResult(
            category="源码", sub_item="基础中间件",
            requirement="从 env.yaml 获取对应架构的 runtime_md5.libc_so 基线值",
            acceptance_criteria="成功获取 libc_so 的 path 和 md5",
        )

        arch = self.config.get("arch")
        if not arch:
            result.fail_test(
                detail="未配置目标架构（arch）",
                remediation="请在 config.yaml 中配置 arch: aarch64/arm32/x86_64/riscv64",
            )
            return result

        if not self._env_data:
            result.fail_test(
                detail="无法获取 env.yaml",
                remediation="请检查 baseline_repo/baseline_branch 配置或网络连接",
            )
            return result

        libc_info = self._get_libc_info()

        if not libc_info:
            result.fail_test(
                detail=f"env.yaml 中未找到 {arch} 架构的 libc_so",
                remediation=f"请更新 env.yaml，添加 {arch} 架构的 runtime_md5.libc_so",
            )
            return result

        baseline_row = (
            f"{'glibc (libc.so)':<22} {'runtime_md5':<18} "
            f"{libc_info.get('path',''):<55} {libc_info.get('md5','')}"
        )
        lines = [
            {"text": "# 基线文件: env.yaml", "color": "#6c7086"},
            {"text": f"# 远端地址: {self._env_url}", "color": "#6c7086"},
            {"text": f"# 目标架构: {arch}", "color": "#6c7086"},
            {"text": "", "color": "#cdd6f4"},
            {"text": f"curl -sL {self._env_url} | grep -A2 'libc_so'", "type": "command"},
            {"text": "", "color": "#cdd6f4"},
            {"text": f"{'检查项':<22} {'所属节':<18} {'路径':<55} {'MD5'}", "color": "#89b4fa"},
            {"text": "-" * 110, "color": "#6c7086"},
            {"text": baseline_row, "color": "#a6e3a1"},
            {"text": "", "color": "#cdd6f4"},
            {"text": f"基线 MD5: {libc_info.get('md5','')}", "type": "success"},
        ]

        path = os.path.join(self._evidence_dir, "middleware_step2_baseline.png")
        render_terminal_screenshot("Step 2: env.yaml 基线（glibc）", lines, path)

        result.pass_test(
            detail=f"成功获取 {arch} 架构 glibc 基线: MD5={libc_info.get('md5','')}",
            evidence=f"url: {self._env_url}, screenshot: {path}",
        )
        return result

    def _step3_compare(self) -> TestResult:
        result = TestResult(
            category="源码", sub_item="基础中间件",
            requirement="对比设备 libc.so MD5 与 env.yaml 中记录的基线值",
            acceptance_criteria="设备 libc.so MD5 与 env.yaml runtime_md5.libc_so 一致",
        )

        arch = self.config.get("arch")
        libc_info = self._get_libc_info()
        expected_md5 = libc_info.get("md5", "") if isinstance(libc_info, dict) else ""

        match = (self._device_md5 == expected_md5) if self._device_md5 and expected_md5 else False

        lines = [
            {"text": "# libc.so MD5 比对结果", "color": "#6c7086"},
            {"text": f"# 架构: {arch}", "color": "#6c7086"},
            {"text": "", "color": "#cdd6f4"},
            {"text": f"{'检查项':<20} {'设备MD5':<34} {'基线MD5':<34} {'结果'}", "color": "#89b4fa"},
            {"text": "-" * 94, "color": "#6c7086"},
        ]

        icon = "✓" if match else "✗"
        color = "#a6e3a1" if match else "#f38ba8"
        status = "一致" if match else "不一致"
        compare_row = (
            f"{icon} {'glibc (libc.so)':<18} "
            f"{(self._device_md5 or 'N/A'):<34} "
            f"{expected_md5:<34} {status}"
        )
        lines.append({"text": compare_row, "color": color})

        lines.append({"text": "", "color": "#cdd6f4"})

        if match:
            lines.append({"text": "设备 libc.so MD5 与基线一致", "type": "success"})
            lines.append({"text": f"  MD5 值均为 {self._device_md5}", "color": "#a6e3a1"})
        else:
            lines.append({"text": "设备 libc.so MD5 与基线不一致", "type": "error"})
            mismatch_detail = (
                f"  设备: {self._device_md5 or 'N/A'}, "
                f"基线: {expected_md5 or 'N/A'}"
            )
            lines.append({"text": mismatch_detail, "color": "#f38ba8"})

        path = os.path.join(self._evidence_dir, "middleware_step3_compare.png")
        render_terminal_screenshot("Step 3: libc.so MD5 比对", lines, path)

        if match:
            result.pass_test(
                detail=f"glibc的MD5值均为{self._device_md5}",
                evidence=f"screenshot: {path}",
            )
        else:
            result.fail_test(
                detail="设备 libc.so MD5 与基线不一致",
                evidence=f"screenshot: {path}",
                remediation="请使用 oee 官方编译链提供的 glibc",
            )
        return result
