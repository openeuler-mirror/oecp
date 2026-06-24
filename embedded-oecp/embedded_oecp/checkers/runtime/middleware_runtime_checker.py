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
import tempfile
from typing import List, Tuple, Optional
from embedded_oecp.checkers import BaseChecker
from embedded_oecp.models import TestResult
from embedded_oecp.utils.shell import run_command, run_remote_command
from embedded_oecp.utils.logger import get_logger
from embedded_oecp.utils.terminal_screenshot import render_terminal_screenshot


ARCH_BINARY_MAP = {
    "aarch64": "glib-abi-check-aarch64",
    "arm32": "glib-abi-check-arm32",
    "arm": "glib-abi-check-arm32",
    "riscv64": "glib-abi-check-riscv64",
    "x86_64": "glib-abi-check-x86",
    "x86-64": "glib-abi-check-x86",
}


class MiddlewareRuntimeChecker(BaseChecker):
    def __init__(self, config: dict, work_dir: str):
        super().__init__(config, work_dir)
        self._evidence_dir = ""

    def run(self) -> List[TestResult]:
        self._evidence_dir = os.path.join(
            self.config.get("output_dir", "/tmp/embedded-oecp/report"), "evidence",
        )
        os.makedirs(self._evidence_dir, exist_ok=True)
        results = []
        results.append(self._check_abi_checksum())
        results.append(self._check_abi_run())
        return results

    def _get_device_cfg(self) -> Tuple[str, str, str, int]:
        cfg = self.config.get("device", {})
        return (
            cfg.get("ip", ""),
            cfg.get("user", "root"),
            cfg.get("password", ""),
            cfg.get("port", 22),
        )

    def _get_arch(self) -> str:
        return self.config.get("arch", "aarch64")

    def _get_binary_name(self) -> str:
        arch = self._get_arch()
        return ARCH_BINARY_MAP.get(arch, f"glib-abi-check-{arch}")

    def _find_local_abi_check_dir(self) -> str:
        source_dir = self.get_source_dir()
        if source_dir:
            d = os.path.join(source_dir, "yocto-meta-openeuler", ".oebuild", "glib2.0-abi-check")
            if os.path.isdir(d):
                return d
        return ""

    def _load_official_md5(self, abi_dir: str, binary_name: str) -> Tuple[str, str]:
        logger = get_logger()
        md5_path = os.path.join(abi_dir, "md5sums")
        if not os.path.isfile(md5_path):
            return "", md5_path
        try:
            with open(md5_path, "r") as f:
                for line in f:
                    parts = line.strip().split(None, 1)
                    if len(parts) == 2 and parts[1] == binary_name:
                        return parts[0], md5_path
        except Exception as e:
            logger.debug(f"Failed to read md5sums: {e}")
        return "", md5_path

    def _check_abi_checksum(self) -> TestResult:
        logger = get_logger()
        result = TestResult(
            category="运行时", sub_item="C库运行时",
            requirement="将 openEuler 官方 ABI 检测程序上传到目标 OS 并验证 MD5 值一致",
            acceptance_criteria="检测的 MD5 值一致",
        )

        host, user, password, port = self._get_device_cfg()
        if not host:
            result.fail_test(detail="未配置目标设备 IP", remediation="请配置 device.ip")
            return result

        arch = self._get_arch()
        binary_name = self._get_binary_name()
        abi_dir = self._find_local_abi_check_dir()

        if not abi_dir:
            result.fail_test(
                detail="未找到本地 glib2.0-abi-check 目录",
                remediation="请确保 source.dir 下存在 yocto-meta-openeuler/.oebuild/glib2.0-abi-check",
            )
            return result

        binary_path = os.path.join(abi_dir, binary_name)
        if not os.path.isfile(binary_path):
            result.fail_test(
                detail=f"未找到 {arch} 架构的检测程序: {binary_name}",
                remediation=f"请确保 glib2.0-abi-check 目录下存在 {binary_name}",
            )
            return result

        official_md5, md5_file_path = self._load_official_md5(abi_dir, binary_name)
        if not official_md5:
            result.fail_test(
                detail=f"md5sums 文件中未找到 {binary_name} 的校验值",
                remediation="请检查 md5sums 文件",
            )
            return result

        remote_path = f"/root/{binary_name}"

        logger.info(f"Uploading {binary_name} to {host}:{remote_path}")
        with open(binary_path, "rb") as bf:
            import paramiko
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, port=port, username=user, password=password)
            sftp = ssh.open_sftp()
            sftp.putfo(bf, remote_path)
            sftp.close()
            ssh.close()

        run_remote_command(host, user, password, f"chmod +x {remote_path}", port=port)

        stdout, stderr, rc = run_remote_command(
            host, user, password, f"md5sum {remote_path}", port=port,
        )
        device_md5 = ""
        if rc == 0:
            parts = stdout.strip().split(None, 1)
            if parts:
                device_md5 = parts[0]

        md5_match = device_md5 == official_md5

        official_lines = [
            {"text": f"# 官方 ABI 检测程序 MD5 校验值 ({md5_file_path})", "color": "#6c7086"},
            {"text": f"# 架构: {arch}", "color": "#6c7086"},
            {"text": "", "color": "#cdd6f4"},
            {"text": f"cat .oebuild/glib2.0-abi-check/md5sums", "type": "command"},
        ]
        try:
            with open(md5_file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(None, 1)
                    if len(parts) == 2:
                        fname = parts[1]
                        md5v = parts[0]
                        if fname == binary_name:
                            official_lines.append({"text": f"  {md5v}  {fname}  <== {arch}", "color": "#a6e3a1"})
                        else:
                            official_lines.append({"text": f"  {md5v}  {fname}", "color": "#6c7086"})
        except Exception:
            official_lines.append({"text": "(读取失败)", "color": "#f38ba8"})

        official_lines.append({"text": "", "color": "#cdd6f4"})
        highlight_text = f"官方 MD5 ({binary_name}): {official_md5}"
        official_lines.append({"text": highlight_text, "color": "#f9e2af", "type": "highlight"})

        path_official = os.path.join(self._evidence_dir, "libc_runtime_step1a_official_md5.png")
        render_terminal_screenshot("Step 1a: 官方 MD5 校验值", official_lines, path_official)

        device_lines = [
            {"text": f"# 目标设备: {user}@{host}", "color": "#6c7086"},
            {"text": f"# 架构: {arch}", "color": "#6c7086"},
            {"text": "", "color": "#cdd6f4"},
            {"text": f"ssh {user}@{host} 'md5sum {remote_path}'", "type": "command"},
        ]
        if device_md5:
            color = "#a6e3a1" if md5_match else "#f38ba8"
            device_lines.append({"text": f"  {stdout.strip()}", "color": color})
        else:
            device_lines.append({"text": f"  md5sum 执行失败: {stderr}", "color": "#f38ba8"})

        device_lines.append({"text": "", "color": "#cdd6f4"})
        device_lines.append({"text": f"设备 MD5: {device_md5}", "color": "#f9e2af", "type": "highlight"})
        device_lines.append({"text": f"官方 MD5: {official_md5}", "color": "#89b4fa"})
        device_lines.append({"text": "", "color": "#cdd6f4"})

        if md5_match:
            device_lines.append({"text": f"MD5 一致: {official_md5}", "type": "success"})
        else:
            device_lines.append({"text": f"MD5 不一致: 设备={device_md5}, 官方={official_md5}", "type": "error"})

        path_device = os.path.join(self._evidence_dir, "libc_runtime_step1b_device_md5.png")
        render_terminal_screenshot("Step 1b: 目标设备 MD5 校验", device_lines, path_device)

        if md5_match:
            evidence = (
                f"official_md5={official_md5}, device_md5={device_md5}, "
                f"screenshot_official={path_official}, "
                f"screenshot_device={path_device}"
            )
            result.pass_test(
                detail=f"ABI 检测程序 MD5 校验通过: {official_md5}",
                evidence=evidence,
            )
        else:
            result.fail_test(
                detail=f"ABI 检测程序 MD5 不一致: 官方={official_md5}, 设备={device_md5}",
                evidence=f"screenshot_official={path_official}, screenshot_device={path_device}",
                remediation="请重新上传检测程序，确保文件完整",
            )

        return result

    def _check_abi_run(self) -> TestResult:
        logger = get_logger()
        result = TestResult(
            category="运行时", sub_item="C库运行时",
            requirement="运行检测程序，验证程序在目标 OS 上正常运行并通过检查",
            acceptance_criteria="检测程序在目标 OS 上正常运行，并通过检查",
        )

        host, user, password, port = self._get_device_cfg()
        if not host:
            result.fail_test(detail="未配置目标设备 IP", remediation="请配置 device.ip")
            return result

        arch = self._get_arch()
        binary_name = self._get_binary_name()
        remote_path = f"/root/{binary_name}"

        run_ok = False
        stdout, stderr, rc = "", "", -1

        stdout_exists, _, rc_exists = run_remote_command(
            host, user, password, f"test -f {remote_path} && echo EXISTS", port=port,
        )
        if rc_exists != 0 or "EXISTS" not in stdout_exists:
            abi_dir = self._find_local_abi_check_dir()
            binary_path = os.path.join(abi_dir, binary_name) if abi_dir else ""
            if not binary_path or not os.path.isfile(binary_path):
                result.fail_test(
                    detail="检测程序未上传且本地未找到",
                    remediation="请先执行 Step 1 上传检测程序",
                )
                return result

            import paramiko
            with open(binary_path, "rb") as bf:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(host, port=port, username=user, password=password)
                sftp = ssh.open_sftp()
                sftp.putfo(bf, remote_path)
                sftp.close()
                ssh.close()
            run_remote_command(host, user, password, f"chmod +x {remote_path}", port=port)

        logger.info(f"Running ABI check on {host}: {remote_path}")
        stdout, stderr, rc = run_remote_command(
            host, user, password, remote_path, port=port, timeout=120,
        )

        run_ok = rc == 0

        lines = [
            {"text": f"# 目标设备: {user}@{host}", "color": "#6c7086"},
            {"text": f"# 架构: {arch}", "color": "#6c7086"},
            {"text": "", "color": "#cdd6f4"},
            {"text": f"ssh {user}@{host} '{remote_path}'", "type": "command"},
        ]

        if stdout and stdout.strip():
            for line in stdout.strip().split("\n"):
                stripped = line.strip()
                if stripped.startswith("[PASS]") or stripped.startswith("[pass]"):
                    lines.append({"text": line, "color": "#a6e3a1"})
                elif stripped.startswith("[FAIL]") or stripped.startswith("[fail]"):
                    lines.append({"text": line, "color": "#f38ba8"})
                elif stripped.startswith("==="):
                    lines.append({"text": line, "color": "#89b4fa"})
                elif stripped.startswith("[") and "]" in stripped:
                    lines.append({"text": line, "color": "#f9e2af"})
                else:
                    lines.append({"text": line, "color": "#cdd6f4"})

        if stderr and stderr.strip():
            lines.append({"text": "", "color": "#cdd6f4"})
            lines.append({"text": "# stderr:", "color": "#6c7086"})
            for line in stderr.strip().split("\n"):
                lines.append({"text": line, "color": "#f38ba8"})

        lines.append({"text": "", "color": "#cdd6f4"})
        lines.append({"text": f"退出码: {rc}", "color": "#89b4fa"})
        lines.append({"text": "", "color": "#cdd6f4"})

        if run_ok:
            lines.append({"text": "ABI 检测程序正常运行，通过检查", "type": "success"})
        else:
            lines.append({"text": f"ABI 检测程序运行失败 (rc={rc})", "type": "error"})

        path = os.path.join(self._evidence_dir, "libc_runtime_step2_abi_run.png")
        render_terminal_screenshot("Step 2: ABI 检测程序运行", lines, path)

        run_remote_command(host, user, password, f"rm -f {remote_path}", port=port)

        if run_ok:
            output_preview = stdout.strip()[:200] if stdout else "(无输出)"
            result.pass_test(
                detail=f"ABI 检测程序在目标设备正常运行: {output_preview}",
                evidence=f"rc={rc}, output={stdout[:300] if stdout else ''}, screenshot={path}",
            )
        else:
            fail_evidence = (
                f"rc={rc}, "
                f"stdout={stdout[:200] if stdout else ''}, "
                f"stderr={stderr[:200] if stderr else ''}, "
                f"screenshot={path}"
            )
            result.fail_test(
                detail=f"ABI 检测程序运行失败: rc={rc}",
                evidence=fail_evidence,
                remediation="请检查目标设备 C 库 ABI 兼容性",
            )

        return result
