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
from typing import List, Tuple
from embedded_oecp.checkers import BaseChecker
from embedded_oecp.models import TestResult
from embedded_oecp.utils.shell import run_command
from embedded_oecp.utils.logger import get_logger
from embedded_oecp.utils.terminal_screenshot import render_terminal_screenshot


class ProjectChecker(BaseChecker):
    def __init__(self, config: dict, work_dir: str):
        super().__init__(config, work_dir)
        self._evidence_dir = ""

    def run(self) -> List[TestResult]:
        self._evidence_dir = os.path.join(
            self.config.get("output_dir", "/tmp/embedded-oecp/report"), "evidence",
        )
        os.makedirs(self._evidence_dir, exist_ok=True)
        results = []
        results.append(self._check_build_command())
        results.append(self._check_build_structure())
        return results

    def _get_build_dir_local(self) -> str:
        d = self.get_build_dir()
        if d and os.path.isdir(d):
            return d
        return ""

    def _run_bitbake_version(self) -> Tuple[str, int]:
        build_dir = self._get_build_dir_local()
        if not build_dir:
            return "", -1
        stdout, stderr, rc = run_command(
            "oebuild bitbake --version", cwd=build_dir, timeout=60,
        )
        output = (stdout or "") + (stderr or "")
        return output.strip(), rc

    def _check_build_command(self) -> TestResult:
        logger = get_logger()
        result = TestResult(
            category="构建", sub_item="构建工程",
            requirement="构建命令 oebuild bitbake 可用",
            acceptance_criteria="oebuild bitbake --version 输出 BitBake Build Tool Core version",
        )

        build_dir = self._get_build_dir_local()
        if not build_dir:
            result.fail_test(
                detail="未配置构建工程目录",
                remediation="请使用 -d 指定构建工程目录",
            )
            return result

        output, rc = self._run_bitbake_version()
        bitbake_ver = ""
        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("INFO - BitBake Build Tool Core version"):
                bitbake_ver = line.split("INFO - ")[-1] if "INFO - " in line else line
                break
            if "BitBake Build Tool Core version" in line:
                bitbake_ver = line.split(" - ")[-1] if " - " in line else line
                break

        lines = [
            {"text": "# 构建命令检查", "color": "#6c7086"},
            {"text": f"# 构建目录: {build_dir}", "color": "#6c7086"},
            {"text": "", "color": "#cdd6f4"},
            {"text": f"$ oebuild bitbake --version", "type": "command"},
        ]

        for line in output.split("\n"):
            stripped = line.strip()
            if stripped:
                if "BitBake Build Tool Core version" in stripped:
                    lines.append({"text": stripped, "color": "#a6e3a1"})
                elif "ERROR" in stripped:
                    lines.append({"text": stripped, "color": "#f38ba8"})
                else:
                    lines.append({"text": stripped, "color": "#6c7086"})

        lines.append({"text": "", "color": "#cdd6f4"})
        if bitbake_ver:
            lines.append({"text": f"✓ {bitbake_ver}", "color": "#a6e3a1"})
            lines.append({"text": "", "color": "#cdd6f4"})
            lines.append({"text": "oebuild bitbake 命令可用", "type": "success"})
        else:
            lines.append({"text": "✗ 未检测到 BitBake 版本信息", "color": "#f38ba8"})
            lines.append({"text": "", "color": "#cdd6f4"})
            lines.append({"text": "oebuild bitbake 命令不可用", "type": "error"})

        path = os.path.join(self._evidence_dir, "project_step1_build_command.png")
        render_terminal_screenshot("Step 1: 构建命令检查", lines, path)

        if bitbake_ver:
            result.pass_test(
                detail=f"oebuild bitbake --version 输出: {bitbake_ver}",
                evidence=f"build_dir: {build_dir}, version: {bitbake_ver}, screenshot: {path}",
            )
        else:
            result.fail_test(
                detail="oebuild bitbake --version 未输出 BitBake 版本信息",
                evidence=f"rc={rc}, output={output[:200]}, screenshot: {path}",
                remediation="请在构建工程目录下执行 oebuild bitbake --version 确认可用",
            )

        return result

    def _check_build_structure(self) -> TestResult:
        logger = get_logger()
        result = TestResult(
            category="构建", sub_item="构建工程",
            requirement="构建目录结构标准",
            acceptance_criteria="包含 cache/conf/output/tmp 目录，conf 下有 bblayers.conf"
                               " 与 local.conf，存在 compile.yaml/.env/oebuild.log",
        )

        build_dir = self._get_build_dir_local()
        if not build_dir:
            result.fail_test(
                detail="未配置构建工程目录",
                remediation="请使用 -d 指定构建工程目录",
            )
            return result

        required_dirs = ["cache", "conf", "output", "tmp"]
        required_conf_files = ["conf/bblayers.conf", "conf/local.conf"]
        required_root_files = ["compile.yaml", ".env", "oebuild.log"]

        missing_dirs = []
        found_dirs = []
        for d in required_dirs:
            if os.path.isdir(os.path.join(build_dir, d)):
                found_dirs.append(d)
            else:
                missing_dirs.append(d)

        missing_conf = []
        found_conf = []
        for f in required_conf_files:
            if os.path.isfile(os.path.join(build_dir, f)):
                found_conf.append(f)
            else:
                missing_conf.append(f)

        missing_root = []
        found_root = []
        for f in required_root_files:
            if os.path.isfile(os.path.join(build_dir, f)):
                found_root.append(f)
            else:
                missing_root.append(f)

        all_ok = not missing_dirs and not missing_conf and not missing_root

        lines = [
            {"text": "# 构建目录结构检查", "color": "#6c7086"},
            {"text": f"# 目录: {build_dir}", "color": "#6c7086"},
            {"text": "", "color": "#cdd6f4"},
            {"text": f"ls {build_dir}/", "type": "command"},
        ]

        if os.path.isdir(build_dir):
            for entry in sorted(os.listdir(build_dir)):
                full = os.path.join(build_dir, entry)
                marker = "d" if os.path.isdir(full) else "-"
                color = "#89b4fa" if os.path.isdir(full) else "#cdd6f4"
                lines.append({"text": f"  {marker} {entry}", "color": color})

        lines.append({"text": "", "color": "#cdd6f4"})
        lines.append({"text": "# 目录检查", "color": "#6c7086"})
        for d in required_dirs:
            exists = os.path.isdir(os.path.join(build_dir, d))
            icon = "✓" if exists else "✗"
            color = "#a6e3a1" if exists else "#f38ba8"
            lines.append({"text": f"  {icon} {d}/", "color": color})

        lines.append({"text": "", "color": "#cdd6f4"})
        lines.append({"text": "# conf/ 文件检查", "color": "#6c7086"})
        for f in required_conf_files:
            exists = os.path.isfile(os.path.join(build_dir, f))
            icon = "✓" if exists else "✗"
            color = "#a6e3a1" if exists else "#f38ba8"
            lines.append({"text": f"  {icon} {f}", "color": color})

        lines.append({"text": "", "color": "#cdd6f4"})
        lines.append({"text": "# 编译文件检查", "color": "#6c7086"})
        for f in required_root_files:
            exists = os.path.isfile(os.path.join(build_dir, f))
            icon = "✓" if exists else "✗"
            color = "#a6e3a1" if exists else "#f38ba8"
            lines.append({"text": f"  {icon} {f}", "color": color})

        lines.append({"text": "", "color": "#cdd6f4"})
        if all_ok:
            lines.append({"text": "构建目录结构符合标准", "type": "success"})
        else:
            missing = missing_dirs + missing_conf + missing_root
            lines.append({"text": f"缺少: {', '.join(missing)}", "type": "error"})

        path = os.path.join(self._evidence_dir, "project_step2_build_structure.png")
        render_terminal_screenshot("Step 2: 构建目录结构检查", lines, path)

        if all_ok:
            result.pass_test(
                detail="构建目录结构符合标准",
                evidence=f"dirs: {found_dirs}, conf: {found_conf}, root: {found_root}, screenshot: {path}",
            )
        else:
            missing = missing_dirs + missing_conf + missing_root
            evidence = (
                f"missing_dirs: {missing_dirs}, "
                f"missing_conf: {missing_conf}, "
                f"missing_root: {missing_root}, "
                f"screenshot: {path}"
            )
            result.fail_test(
                detail=f"构建目录结构不完整，缺少: {', '.join(missing)}",
                evidence=evidence,
                remediation="请确保构建工程目录完整",
            )

        return result
