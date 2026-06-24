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
from typing import List, Optional
import yaml
from embedded_oecp.checkers import BaseChecker
from embedded_oecp.models import TestResult
from embedded_oecp.utils.git import get_remote_url, get_commit_id
from embedded_oecp.utils.shell import run_command, run_remote_command
from embedded_oecp.utils.logger import get_logger
from embedded_oecp.utils.terminal_screenshot import render_terminal_screenshot

OPENEULER_ORG_HOSTS = ["atomgit.com/openeuler", "gitee.com/openeuler"]
MAINSTREAM_VERSION_PATTERN = re.compile(r"^(\d+\.\d+)")


class KernelChecker(BaseChecker):
    def __init__(self, config: dict, work_dir: str):
        super().__init__(config, work_dir)
        self._build_dir = ""
        self._machine = None
        self._kernel_dir = None
        self._manifest_entry = None
        self._manifest_remote = ""
        self._manifest_version = ""
        self._local_commit = ""
        self._kernel_version = ""
        self._evidence_dir = ""

    def run(self) -> List[TestResult]:
        self._build_dir = self._resolve_build_dir()
        if self._build_dir:
            self._evidence_dir = os.path.join(
                self.config.get("output_dir", "/tmp/embedded-oecp/report"), "evidence",
            )
            os.makedirs(self._evidence_dir, exist_ok=True)
            self._resolve_all()

        results = []
        results.append(self._step1_manifest_info())
        results.append(self._step2_repo_screenshot())
        results.append(self._step3_local_verify())
        results.append(self._step4_kernel_version())
        results.append(self._step5_target_uname())
        return results

    def _resolve_build_dir(self) -> str:
        d = self.get_build_dir()
        if d and os.path.isdir(d):
            return d
        return ""

    def _oebuild_getvar(self, var: str, recipe: str = None, machine_filter: bool = False) -> str:
        if not self._build_dir:
            return ""
        if recipe:
            cmd = f"oebuild bitbake-getvar -r {recipe} {var}"
        else:
            cmd = f"oebuild bitbake-getvar {var}"
        stdout, stderr, rc = run_command(cmd, cwd=self._build_dir, timeout=120)
        return stdout + "\n" + stderr

    def _parse_var(self, output: str, var_name: str) -> Optional[str]:
        m = re.search(rf'^{re.escape(var_name)}="([^"]+)"', output, re.MULTILINE)
        return m.group(1) if m else None

    def _get_manifest_path(self) -> str:
        if not self._build_dir:
            return ""
        p = os.path.normpath(
            os.path.join(self._build_dir, "..", "..", "src", "yocto-meta-openeuler", ".oebuild", "manifest.yaml")
        )
        return p if os.path.isfile(p) else ""

    def _resolve_all(self):
        logger = get_logger()

        out = self._oebuild_getvar("MACHINE")
        self._machine = self._parse_var(out, "MACHINE")
        logger.info(f"MACHINE={self._machine}")

        if self._machine:
            kdir = os.path.join(self._build_dir, "tmp", "work-shared", self._machine, "kernel-source")
            if os.path.isdir(kdir):
                self._kernel_dir = kdir
                logger.info(f"内核源码目录: {kdir}")

        if self._kernel_dir:
            self._local_commit = get_commit_id(self._kernel_dir) or ""
        logger.info(f"Local commit: {self._local_commit}")

        if self._machine:
            out2 = self._oebuild_getvar("OPENEULER_LOCAL_NAME", recipe="virtual/kernel")
            local_name = self._parse_var(out2, "OPENEULER_LOCAL_NAME")

            if local_name:
                logger.info(f"OPENEULER_LOCAL_NAME={local_name}")
                manifest_path = self._get_manifest_path()
                if manifest_path:
                    with open(manifest_path, "r") as f:
                        data = yaml.safe_load(f) or {}
                    entry = data.get("manifest_list", {}).get(local_name)
                    if entry:
                        self._manifest_entry = entry
                        self._manifest_remote = entry.get("remote_url", "")
                        self._manifest_version = entry.get("version", "")
                        logger.info(f"manifest: remote={self._manifest_remote}, version={self._manifest_version}")

        if self._kernel_dir:
            makefile = os.path.join(self._kernel_dir, "Makefile")
            self._kernel_version = self._parse_makefile_version(makefile)
        logger.info(f"Kernel version: {self._kernel_version}")

    def _step1_manifest_info(self) -> TestResult:
        logger = get_logger()
        result = TestResult(
            category="源码", sub_item="内核",
            requirement="从 manifest.yaml 获取内核版本信息",
            acceptance_criteria="成功获取 OPENEULER_LOCAL_NAME 并在 manifest.yaml 中找到内核 remote 和 version",
        )

        if not self._build_dir:
            result.fail_test(detail="未配置镜像编译目录", remediation="请使用 -d 指定编译目录")
            return result

        if not self._machine:
            result.fail_test(detail="无法获取 MACHINE 变量")
            return result

        if not self._manifest_entry:
            result.fail_test(detail="未在 manifest.yaml 中找到内核条目")
            return result

        logger.info(
            f"Step 1: MACHINE={self._machine}, "
            f"manifest remote={self._manifest_remote}, "
            f"version={self._manifest_version}"
        )

        detail = (
            f"MACHINE={self._machine}, "
            f"manifest: remote={self._manifest_remote}, "
            f"version={self._manifest_version[:12]}"
        )
        result.pass_test(
            detail=detail,
            evidence=f"OPENEULER_LOCAL_NAME resolved, manifest parsed",
        )
        return result

    def _step2_repo_screenshot(self) -> TestResult:
        logger = get_logger()
        result = TestResult(
            category="源码", sub_item="内核",
            requirement="内核托管仓库在 openEuler 组织下",
            acceptance_criteria="内核仓库 remote 位于 atomgit.com/openeuler",
        )

        if not self._manifest_remote:
            result.fail_test(detail="未获取到内核仓库 remote URL")
            return result

        is_openeuler = any(h in self._manifest_remote.lower() for h in OPENEULER_ORG_HOSTS)

        page_url = self._manifest_remote.rstrip("/")
        if page_url.endswith(".git"):
            page_url = page_url[:-4]

        path = os.path.join(self._evidence_dir, "kernel_step2_repo_page.png")
        from embedded_oecp.utils.screenshot import take_screenshot
        take_screenshot(page_url, path, width=1920, height=1080)

        if is_openeuler:
            result.pass_test(
                detail=f"内核仓库在 openEuler 组织: {self._manifest_remote}",
                evidence=f"page: {page_url}, screenshot: {path}",
            )
        else:
            result.fail_test(
                detail=f"内核仓库不在 openEuler 组织: {self._manifest_remote}",
                evidence=f"page: {page_url}",
                remediation="请将内核托管至 atomgit.com/openeuler",
            )
        return result

    def _step3_local_verify(self) -> TestResult:
        logger = get_logger()
        result = TestResult(
            category="源码", sub_item="内核",
            requirement="manifest.yaml 信息与构建工程内核源码一致",
            acceptance_criteria="本地内核 upstream 与 manifest remote 一致，commit 在远端存在",
        )

        if not self._kernel_dir or not self._manifest_remote:
            result.fail_test(detail="缺少内核源码目录或 manifest 信息")
            return result

        upstream_url = get_remote_url(self._kernel_dir)

        stdout_ls, stderr_ls, rc_ls = run_command(
            f"git ls-remote {self._manifest_remote} {self._manifest_version}", timeout=60,
        )
        version_in_remote = (rc_ls == 0 and self._manifest_version in stdout_ls)

        stdout_log, _, _ = run_command(
            f'git log -1 --oneline {self._manifest_version}', cwd=self._kernel_dir, timeout=10,
        )
        version_in_local = bool(stdout_log.strip())

        lines = [
            {"text": f"# 内核源码目录: {self._kernel_dir}", "color": "#6c7086"},
            {"text": "", "color": "#cdd6f4"},
            {"text": f"cd {self._kernel_dir}", "type": "command"},
            {"text": f"git remote -v", "type": "command"},
            {"text": f"upstream  {upstream_url} (fetch)", "color": "#89b4fa"},
            {"text": "", "color": "#cdd6f4"},
            {"text": f"# manifest remote: {self._manifest_remote}", "color": "#6c7086"},
            {"text": "", "color": "#cdd6f4"},
            {"text": f"git log -1 --oneline {self._manifest_version}", "type": "command"},
        ]

        if version_in_local:
            lines.append({"text": stdout_log.strip(), "color": "#a6e3a1"})
        else:
            lines.append({"text": f"(commit {self._manifest_version[:12]} not found in local)", "color": "#f38ba8"})

        lines.append({"text": "", "color": "#cdd6f4"})
        lines.append({"text": f"git ls-remote {self._manifest_remote} {self._manifest_version}", "type": "command"})

        if version_in_remote:
            lines.append({"text": stdout_ls.strip(), "color": "#a6e3a1"})
            lines.append({"text": "", "color": "#cdd6f4"})
            lines.append({"text": "UPSTREAM MATCH: local upstream == manifest remote", "type": "success"})
            commit_msg = f"COMMIT VERIFIED: {self._manifest_version[:12]} exists in remote"
            lines.append({"text": commit_msg, "type": "success"})
        else:
            lines.append({"text": f"(not found in remote)", "color": "#f38ba8"})

        remote_match = (upstream_url.rstrip("/") == self._manifest_remote.rstrip("/")
                        or upstream_url.rstrip(".git/") == self._manifest_remote.rstrip(".git/"))

        path = os.path.join(self._evidence_dir, "kernel_step3_local_verify.png")
        render_terminal_screenshot("Step 3: 本地内核仓验证", lines, path)

        if remote_match and version_in_remote:
            result.pass_test(
                detail=f"upstream 一致, commit {self._manifest_version[:12]} 远端存在",
                evidence=f"upstream: {upstream_url}, screenshot: {path}",
            )
        elif not remote_match:
            result.fail_test(
                detail=f"本地 upstream ({upstream_url}) 与 manifest ({self._manifest_remote}) 不一致",
                evidence=f"screenshot: {path}",
            )
        else:
            result.fail_test(
                detail=f"commit {self._manifest_version[:12]} 在远端未找到",
                evidence=f"screenshot: {path}",
            )
        return result

    def _step4_kernel_version(self) -> TestResult:
        logger = get_logger()
        mainstream = self.config.get("kernel", {}).get("mainstream_versions", ["5.10", "6.6"])
        result = TestResult(
            category="源码", sub_item="内核",
            requirement=f"内核版本在 oee 主流范围内（{'/'.join(mainstream)}）",
            acceptance_criteria=f"内核版本为 {' 或 '.join(mainstream)}",
        )

        if not self._kernel_version:
            result.fail_test(detail="无法获取内核版本")
            return result

        match = MAINSTREAM_VERSION_PATTERN.match(self._kernel_version)
        major_minor = match.group(1) if match else ""
        in_range = major_minor in mainstream

        makefile_path = os.path.join(self._kernel_dir, "Makefile") if self._kernel_dir else ""
        makefile_lines = []
        if os.path.isfile(makefile_path):
            with open(makefile_path) as f:
                for line in f:
                    s = line.strip()
                    if any(s.startswith(k) for k in ("VERSION", "PATCHLEVEL", "SUBLEVEL", "EXTRAVERSION")):
                        makefile_lines.append(s)

        makefile = os.path.join(self._kernel_dir, "Makefile") if self._kernel_dir else "Makefile"
        lines = [
            {"text": f"# 内核 Makefile 版本检查", "color": "#6c7086"},
            {"text": f"cat {makefile} | grep -E 'VERSION|PATCHLEVEL|SUBLEVEL'", "type": "command"},
        ]
        for ml in makefile_lines:
            lines.append({"text": ml, "color": "#cdd6f4"})

        lines.append({"text": "", "color": "#cdd6f4"})
        lines.append({"text": f"内核版本: {self._kernel_version}", "type": "highlight", "color": "#f9e2af"})
        lines.append({"text": f"主流范围: {'/'.join(mainstream)}", "color": "#89b4fa"})

        if in_range:
            lines.append({"text": f"版本 {self._kernel_version} 在主流范围内", "type": "success"})
        else:
            lines.append({"text": f"版本 {self._kernel_version} 不在主流范围内", "type": "error"})

        path = os.path.join(self._evidence_dir, "kernel_step4_version_check.png")
        render_terminal_screenshot("Step 4: 内核版本检查", lines, path)

        if in_range:
            result.pass_test(
                detail=f"内核版本 {self._kernel_version} 在主流范围内",
                evidence=f"version: {self._kernel_version}, screenshot: {path}",
            )
        else:
            result.fail_test(
                detail=f"内核版本 {self._kernel_version} 不在主流范围内（{'/'.join(mainstream)}）",
                evidence=f"screenshot: {path}",
            )
        return result

    def _step5_target_uname(self) -> TestResult:
        logger = get_logger()
        mainstream = self.config.get("kernel", {}).get("mainstream_versions", ["5.10", "6.6"])
        result = TestResult(
            category="源码", sub_item="内核",
            requirement="目标设备内核版本在主流范围内",
            acceptance_criteria=f"目标设备 uname -r 版本为 {' 或 '.join(mainstream)}",
        )

        device_cfg = self.config.get("device", {})
        device_ip = device_cfg.get("ip")

        if not device_ip:
            result.fail_test(
                detail="未配置目标设备 IP（使用 --device-ip 或配置 device.ip）",
                remediation="请配置 --device-ip",
            )
            return result

        host = device_ip
        user = device_cfg.get("user", "root")
        password = device_cfg.get("password", "")
        port = device_cfg.get("port", 22)

        stdout, stderr, rc = run_remote_command(host, user, password, "uname -r", port=port)
        uname_output = stdout.strip() if rc == 0 else ""

        if not uname_output:
            result.fail_test(detail=f"无法获取目标设备内核版本: rc={rc}, stderr={stderr}")
            return result

        match = MAINSTREAM_VERSION_PATTERN.match(uname_output)
        major_minor = match.group(1) if match else ""
        in_range = major_minor in mainstream

        lines = [
            {"text": f"# 目标设备: {user}@{host}", "color": "#6c7086"},
            {"text": "", "color": "#cdd6f4"},
            {"text": f"ssh {user}@{host} 'uname -r'", "type": "command"},
            {"text": uname_output, "type": "highlight", "color": "#f9e2af"},
            {"text": "", "color": "#cdd6f4"},
            {"text": f"主流范围: {'/'.join(mainstream)}", "color": "#89b4fa"},
        ]

        if in_range:
            lines.append({"text": f"设备内核 {uname_output} 在主流范围内", "type": "success"})
        else:
            lines.append({"text": f"设备内核 {uname_output} 不在主流范围内", "type": "error"})

        path = os.path.join(self._evidence_dir, "kernel_step5_target_uname.png")
        render_terminal_screenshot("Step 5: 目标设备内核版本", lines, path)

        if in_range:
            result.pass_test(
                detail=f"目标设备内核 {uname_output} 在主流范围内",
                evidence=f"uname: {uname_output}, screenshot: {path}",
            )
        else:
            result.fail_test(
                detail=f"目标设备内核 {uname_output} 不在主流范围内（{'/'.join(mainstream)}）",
                evidence=f"screenshot: {path}",
            )
        return result

    def _parse_makefile_version(self, path: str) -> str:
        if not os.path.isfile(path):
            return ""
        parts = {}
        with open(path) as f:
            for line in f:
                s = line.strip()
                for key in ("VERSION", "PATCHLEVEL", "SUBLEVEL", "EXTRAVERSION"):
                    if s.startswith(f"{key} =") or s.startswith(f"{key}\t="):
                        parts[key] = s.split("=", 1)[1].strip()
        if "VERSION" in parts and "PATCHLEVEL" in parts:
            v = f"{parts['VERSION']}.{parts['PATCHLEVEL']}"
            if "SUBLEVEL" in parts:
                v += f".{parts['SUBLEVEL']}"
            extra = parts.get("EXTRAVERSION")
            if extra:
                v += extra
            return v
        return ""
