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
from embedded_oecp.utils.env_yaml import load_env_yaml, get_toolchain_md5, get_runtime_md5, build_env_yaml_url
from embedded_oecp.utils.md5 import compute_file_md5
from embedded_oecp.utils.logger import get_logger
from embedded_oecp.utils.terminal_screenshot import render_terminal_screenshot
from embedded_oecp.utils.screenshot import take_screenshot

CHECK_ITEMS = {
    "gcc": {
        "section": "toolchain_md5",
        "display_name": "gcc",
    },
    "libc_so": {
        "section": "runtime_md5",
        "display_name": "glibc (libc.so.6)",
    },
}


class CompilerChecker(BaseChecker):
    def __init__(self, config: dict, work_dir: str):
        super().__init__(config, work_dir)
        self._evidence_dir = ""
        self._env_data = None
        self._env_url = ""
        self._env_page_url = ""

    def run(self) -> List[TestResult]:
        self._evidence_dir = os.path.join(
            self.config.get("output_dir", "/tmp/embedded-oecp/report"), "evidence",
        )
        os.makedirs(self._evidence_dir, exist_ok=True)

        baseline_repo = self.config.get("baseline_repo", "")
        baseline_branch = self.config.get("baseline_branch", "")
        self._env_url = build_env_yaml_url(baseline_repo, baseline_branch)

        import re
        m = re.match(r'https?://[^/]+/([^/]+/[^/]+?)(?:\.git)?$', baseline_repo)
        if m:
            self._env_page_url = f"https://atomgit.com/{m.group(1)}/blob/{baseline_branch}/.oebuild/env.yaml"

        self._env_data = load_env_yaml(self.work_dir, baseline_repo, baseline_branch)

        results = []
        results.append(self._step1_baseline())
        results.append(self._step2_toolchain_md5())
        results.append(self._step3_conclusion())
        return results

    def _get_toolchain_dir(self) -> str:
        toolchain_dir = self.config.get("toolchain", {}).get("dir")
        if toolchain_dir and os.path.isdir(toolchain_dir):
            return toolchain_dir
        arch = self.config.get("arch", "")
        arch_dir_map = {
            "aarch64": "/usr1/openeuler/gcc/openeuler_gcc_arm64le",
            "arm32": "/usr1/openeuler/gcc/openeuler_gcc_arm32le",
            "x86_64": "/usr1/openeuler/gcc/openeuler_gcc_x86_64le",
            "riscv64": "/usr1/openeuler/gcc/openeuler_gcc_riscv64le",
        }
        if arch in arch_dir_map:
            d = arch_dir_map[arch]
            if os.path.isdir(d):
                return d
        build_dir = self.get_build_dir()
        if build_dir:
            base = os.path.normpath(os.path.join(build_dir, "..", ".."))
            for sub in ["gcc/openeuler_gcc_arm64le", "gcc"]:
                gcc_dir = os.path.join(base, sub)
                if os.path.isdir(gcc_dir):
                    return gcc_dir
        return ""

    def _get_check_info(self, key):
        arch = self.config.get("arch")
        runtime_md5 = get_runtime_md5(self._env_data, arch)
        toolchain_md5 = get_toolchain_md5(self._env_data, arch)
        item_meta = CHECK_ITEMS[key]
        if item_meta["section"] == "toolchain_md5":
            return toolchain_md5.get(key, {})
        else:
            return runtime_md5.get(key, {})

    def _step1_baseline(self) -> TestResult:
        logger = get_logger()
        result = TestResult(
            category="构建", sub_item="编译链",
            requirement="从远端 env.yaml 获取 gcc 和 glibc MD5 基线",
            acceptance_criteria="成功获取 toolchain_md5.gcc 和 runtime_md5.libc_so",
        )

        arch = self.config.get("arch")
        if not arch:
            result.fail_test(
                detail="未配置目标架构（arch）",
                remediation="请使用 --arch aarch64 或配置 arch",
            )
            return result

        if not self._env_data:
            result.fail_test(
                detail="无法获取 env.yaml（local 和 remote 均失败）",
                remediation="请检查 baseline_repo/baseline_branch 配置",
            )
            return result

        gcc_info = self._get_check_info("gcc")
        libc_info = self._get_check_info("libc_so")

        if not gcc_info or not libc_info:
            result.fail_test(
                detail=f"env.yaml 中未找到 {arch} 架构的 gcc 或 libc_so",
            )
            return result

        if self._env_page_url:
            screenshot_path = os.path.join(self._evidence_dir, "compiler_step1_env_yaml.png")
            try:
                take_screenshot(self._env_page_url, screenshot_path)
                logger.info(f"env.yaml page screenshot saved")
            except Exception as e:
                logger.warning(f"Web screenshot failed: {e}, using terminal fallback")
                screenshot_path = None
        else:
            screenshot_path = None

        if not screenshot_path:
            lines = [
                {"text": "# env.yaml 基线（gcc + glibc MD5）", "color": "#6c7086"},
                {"text": f"# 远端地址: {self._env_url}", "color": "#6c7086"},
                {"text": f"# 目标架构: {arch}", "color": "#6c7086"},
                {"text": "", "color": "#cdd6f4"},
                {"text": f"{'检查项':<22} {'所属节':<18} {'路径':<55} {'MD5'}", "color": "#89b4fa"},
                {"text": "-" * 110, "color": "#6c7086"},
            ]
            for key in ["gcc", "libc_so"]:
                info = self._get_check_info(key)
                item_meta = CHECK_ITEMS[key]
                if isinstance(info, dict):
                    text = (f"{item_meta['display_name']:<22} {item_meta['section']:<18} "
                            f"{info.get('path',''):<55} {info.get('md5','')}")
                    lines.append({"text": text, "color": "#a6e3a1"})

            lines.append({"text": "", "color": "#cdd6f4"})
            lines.append({"text": "成功获取 gcc 和 glibc MD5 基线（2 项）", "type": "success"})

            screenshot_path = os.path.join(self._evidence_dir, "compiler_step1_env_yaml.png")
            render_terminal_screenshot("Step 1: env.yaml 编译链基线（gcc+glibc）", lines, screenshot_path)

        result.pass_test(
            detail=f"成功获取 {arch} 编译链基线: gcc 和 glibc(libc_so) 共 2 项",
            evidence=f"env_url: {self._env_url}, screenshot: {screenshot_path}",
        )
        return result

    def _step2_toolchain_md5(self) -> TestResult:
        logger = get_logger()
        result = TestResult(
            category="构建", sub_item="编译链",
            requirement="计算构建环境中 gcc 和 glibc 文件的 MD5 值",
            acceptance_criteria="成功计算 gcc 和 libc.so.6 的 MD5",
        )

        arch = self.config.get("arch")
        if not arch:
            result.fail_test(detail="未配置目标架构（arch）")
            return result

        if not self._env_data:
            result.fail_test(detail="无 env.yaml 基线数据")
            return result

        toolchain_dir = self._get_toolchain_dir()
        if not toolchain_dir:
            result.fail_test(
                detail="未找到工具链目录",
                remediation="请配置 toolchain.dir 指向工具链根目录",
            )
            return result

        lines = [
            {"text": f"# 构建环境 gcc + glibc MD5 提取", "color": "#6c7086"},
            {"text": f"# 工具链目录: {toolchain_dir}", "color": "#6c7086"},
            {"text": f"# 架构: {arch}", "color": "#6c7086"},
            {"text": "", "color": "#cdd6f4"},
        ]

        all_check_results = []
        for key in ["gcc", "libc_so"]:
            info = self._get_check_info(key)
            item_meta = CHECK_ITEMS[key]
            if not isinstance(info, dict):
                continue
            rel_path = info.get("path", "")
            exp_md5 = info.get("md5", "")
            abs_path = os.path.join(toolchain_dir, rel_path)
            actual_md5 = compute_file_md5(abs_path)

            if actual_md5:
                lines.append({"text": f"$ md5sum {abs_path}", "type": "command"})
                lines.append({"text": f"{actual_md5}  {abs_path}", "color": "#f9e2af", "type": "highlight"})
            else:
                lines.append({"text": f"$ md5sum {abs_path}", "type": "command"})
                lines.append({"text": f"md5sum: {abs_path}: No such file or directory", "color": "#f38ba8"})

            match = (actual_md5 == exp_md5) if actual_md5 else False
            all_check_results.append({
                "section": item_meta["section"],
                "name": key,
                "display_name": item_meta["display_name"],
                "path": rel_path,
                "expected": exp_md5,
                "actual": actual_md5 or "N/A",
                "match": match,
            })

        lines.append({"text": "", "color": "#cdd6f4"})
        found = sum(1 for r in all_check_results if r["actual"] != "N/A")
        success_type = "success" if found == len(all_check_results) else "error"
        found_msg = f"成功提取 {found}/{len(all_check_results)} 个文件 MD5"
        lines.append({"text": found_msg, "type": success_type})

        screenshot_path = os.path.join(self._evidence_dir, "compiler_step2_md5sum.png")
        render_terminal_screenshot("Step 2: 构建环境 gcc + glibc MD5", lines, screenshot_path)

        if found == len(all_check_results):
            result.pass_test(
                detail=f"成功提取 {found} 个文件 MD5（gcc + glibc）",
                evidence=f"screenshot: {screenshot_path}",
            )
        else:
            result.fail_test(
                detail=f"仅提取到 {found}/{len(all_check_results)} 个文件 MD5",
                evidence=f"screenshot: {screenshot_path}",
            )
        return result

    def _step3_conclusion(self) -> TestResult:
        logger = get_logger()
        result = TestResult(
            category="构建", sub_item="编译链",
            requirement="gcc 和 glibc MD5 与 env.yaml 基线一致",
            acceptance_criteria="gcc 和 libc.so.6 的 MD5 与 env.yaml 一致",
        )

        arch = self.config.get("arch")
        if not arch:
            result.fail_test(detail="未配置目标架构（arch）")
            return result

        if not self._env_data:
            result.fail_test(detail="无 env.yaml 基线数据")
            return result

        toolchain_dir = self._get_toolchain_dir()
        if not toolchain_dir:
            result.fail_test(detail="未找到工具链目录")
            return result

        comparison = []
        for key in ["gcc", "libc_so"]:
            info = self._get_check_info(key)
            item_meta = CHECK_ITEMS[key]
            if not isinstance(info, dict):
                continue
            rel_path = info.get("path", "")
            exp_md5 = info.get("md5", "")
            abs_path = os.path.join(toolchain_dir, rel_path)
            actual_md5 = compute_file_md5(abs_path)
            match = (actual_md5 == exp_md5) if actual_md5 else False
            comparison.append({
                "section": item_meta["section"],
                "name": key,
                "display_name": item_meta["display_name"],
                "path": rel_path,
                "expected": exp_md5,
                "actual": actual_md5 or "N/A",
                "match": match,
            })

        all_match = all(c["match"] for c in comparison)

        lines = [
            {"text": "# gcc + glibc MD5 比对结论", "color": "#6c7086"},
            {"text": f"# 架构: {arch}  工具链: {toolchain_dir}", "color": "#6c7086"},
            {"text": "", "color": "#cdd6f4"},
            {"text": f"{'名称':<20} {'分类':<18} {'实际MD5':<34} {'基线MD5':<34} {'结果'}", "color": "#89b4fa"},
            {"text": "-" * 110, "color": "#6c7086"},
        ]

        for c in comparison:
            icon = "✓" if c["match"] else "✗"
            color = "#a6e3a1" if c["match"] else "#f38ba8"
            status = "一致" if c["match"] else "不一致"
            act_short = c["actual"][:32] + ".." if len(c["actual"]) > 32 else c["actual"]
            exp_short = c["expected"][:32] + ".." if len(c["expected"]) > 32 else c["expected"]
            row = (f"{icon} {c['display_name']:<18} {c['section']:<18} "
                   f"{act_short:<34} {exp_short:<34} {status}")
            lines.append({"text": row, "color": color})

        lines.append({"text": "", "color": "#cdd6f4"})
        if all_match:
            matched = sum(1 for c in comparison if c["match"])
            lines.append({"text": f"全部 {matched} 项（gcc + glibc）MD5 与基线一致", "type": "success"})
        else:
            mismatched = [c for c in comparison if not c["match"]]
            lines.append({"text": f"{len(mismatched)}/{len(comparison)} 项 MD5 不一致", "type": "error"})
            for c in mismatched:
                mm = (f"  {c['display_name']}({c['section']}): "
                      f"实际={c['actual'][:16]}..., "
                      f"基线={c['expected'][:16]}...")
                lines.append({"text": mm, "color": "#f38ba8"})

        screenshot_path = os.path.join(self._evidence_dir, "compiler_step3_conclusion.png")
        render_terminal_screenshot("Step 3: gcc + glibc MD5 比对结论", lines, screenshot_path)

        if all_match:
            result.pass_test(
                detail=f"全部 {len(comparison)} 项（gcc + glibc）MD5 与基线一致",
                evidence=f"screenshot: {screenshot_path}",
            )
        else:
            mismatched = [c for c in comparison if not c["match"]]
            result.fail_test(
                detail=f"{len(mismatched)}/{len(comparison)} 项 MD5 不一致",
                evidence=f"screenshot: {screenshot_path}",
                remediation="请使用 oee 官方编译链",
            )
        return result
