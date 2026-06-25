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
import json
import time
import subprocess
from typing import List, Tuple
from embedded_oecp.checkers import BaseChecker
from embedded_oecp.models import TestResult
from embedded_oecp.utils.shell import run_command
from embedded_oecp.utils.logger import get_logger
from embedded_oecp.utils.terminal_screenshot import render_terminal_screenshot


class ATTestChecker(BaseChecker):
    def __init__(self, config: dict, work_dir: str):
        super().__init__(config, work_dir)
        self._evidence_dir = ""

    def run(self) -> List[TestResult]:
        self._evidence_dir = os.path.join(
            self.config.get("output_dir", "/tmp/embedded-oecp/report"), "evidence",
        )
        os.makedirs(self._evidence_dir, exist_ok=True)
        results = []
        results.append(self._check_at_tests())
        return results

    def _ensure_mugen(self) -> str:
        logger = get_logger()
        mugen_cfg = self.config.get("mugen", {})
        mugen_dir = mugen_cfg.get("dir")

        if mugen_dir and os.path.isfile(os.path.join(mugen_dir, "combination.sh")):
            logger.info(f"Using existing mugen: {mugen_dir}")
            return mugen_dir

        remote = mugen_cfg.get("remote", "https://atomgit.com/openeuler/mugen.git")
        branch = mugen_cfg.get("branch", "master")
        mugen_dir = os.path.join(self.work_dir, "mugen")

        if os.path.isfile(os.path.join(mugen_dir, "combination.sh")):
            logger.info(f"Using cached mugen: {mugen_dir}")
            mugen_cfg["dir"] = mugen_dir
            return mugen_dir

        logger.info(f"Cloning mugen from {remote} branch {branch}")
        stdout, stderr, rc = run_command(
            f"git clone --depth 1 -b {branch} {remote} {mugen_dir}",
            timeout=300,
        )
        if rc != 0:
            logger.error(f"Failed to clone mugen: {stderr}")
            return ""

        mugen_cfg["dir"] = mugen_dir
        return mugen_dir

    def _ensure_suite2cases(self, mugen_dir: str):
        logger = get_logger()
        suite_dir = os.path.join(mugen_dir, "suite2cases")
        embedded_files = []
        for f in os.listdir(suite_dir):
            if not f.startswith("embedded_"):
                continue
            stripped = f.replace("embedded_", "", 1)
            stripped = stripped.replace(".json", "").replace("_", "")
            stripped = stripped.replace("test", "").replace("extra", "")
            if "_" not in stripped:
                embedded_files.append(f)

        needed = ["embedded_os_basic_test.json", "embedded_os_basic_extra_test.json",
                   "embedded_security_config_test.json", "embedded_application_develop_tests.json"]
        missing = [f for f in needed if not os.path.isfile(os.path.join(suite_dir, f))]
        if not missing:
            return

        logger.info(f"Missing suite2cases files: {missing}, copying from source mugen")
        src_candidates = [
            os.path.join(os.path.dirname(mugen_dir), "demo", "mugen"),
            "/home/ubuntu/demo/mugen",
        ]
        for src in src_candidates:
            src_suite = os.path.join(src, "suite2cases")
            if os.path.isdir(src_suite):
                for f in missing:
                    src_f = os.path.join(src_suite, f)
                    if os.path.isfile(src_f):
                        import shutil
                        shutil.copy2(src_f, suite_dir)
                        logger.info(f"Copied {f} from {src}")
                break

    def _install_sdk(self) -> str:
        logger = get_logger()
        sdk_file = self.config.get("sdk_file", "")
        if not sdk_file or not os.path.isfile(sdk_file):
            return ""

        sdk_install_base = self.config.get("mugen", {}).get("sdk_install_dir", "/opt/sdk")
        machine = self._get_machine()
        sdk_path = os.path.join(sdk_install_base, machine)

        if os.path.isfile(os.path.join(sdk_path, "environment-setup-cortexa72-openeuler-linux")):
            logger.info(f"SDK already installed at {sdk_path}")
            return sdk_path

        os.makedirs(sdk_install_base, exist_ok=True)

        logger.info(f"Installing SDK: {sdk_file} -> {sdk_path}")
        os.chmod(sdk_file, 0o755)
        proc = subprocess.run(
            [sdk_file],
            input=sdk_path + "\n",
            capture_output=True, text=True, timeout=600,
        )
        stdout, stderr, rc = proc.stdout, proc.stderr, proc.returncode

        if rc != 0:
            logger.warning(f"SDK install may have issues: rc={rc}, stderr={stderr}")
            if os.path.isdir(sdk_path):
                env_files = [f for f in os.listdir(sdk_path) if f.startswith("environment-setup")]
                if env_files:
                    return sdk_path
            return ""

        return sdk_path

    def _get_machine(self) -> str:
        build_dir = self.get_build_dir()
        if build_dir:
            return os.path.basename(build_dir)
        return "target"

    def _prepare_at_config(self, mugen_dir: str, sdk_path: str) -> str:
        logger = get_logger()
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "assets", "embedded_osv_at.json",
        )

        if not os.path.isfile(template_path):
            logger.error(f"AT config template not found: {template_path}")
            return ""

        with open(template_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        device_cfg = self.config.get("device", {})
        machine = self._get_machine()

        if config.get("env") and len(config["env"]) > 0:
            env = config["env"][0]
            env["name"] = machine
            env["ip"] = device_cfg.get("ip", "")
            env["password"] = device_cfg.get("password", "")
            env["port"] = str(device_cfg.get("port", 22))
            env["user"] = device_cfg.get("user", "root")
            if sdk_path:
                env["sdk_path"] = sdk_path

        for exe in config.get("execute", []):
            if "env" in exe and exe["env"]:
                exe["env"] = [machine]

        config_path = os.path.join(mugen_dir, "combination", "embedded_osv_at.json")
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

        logger.info(f"AT config prepared: {config_path}")
        return config_path

    def _run_at_tests(self, mugen_dir: str, config_path: str) -> Tuple[str, int, str, str]:
        logger = get_logger()
        cmd_list = ["bash", "combination.sh", "-f", config_path, "-r"]
        cmd = " ".join(cmd_list)
        logger.info(f"Running: {cmd} in {mugen_dir}")

        try:
            proc = subprocess.Popen(
                cmd_list, cwd=mugen_dir,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
        except Exception as e:
            logger.error(f"Failed to start AT tests: {e}")
            return cmd, -1, "", str(e)

        stdout_lines = []
        start_time = time.time()
        cases_done = 0

        logger.info(f"\n{'='*60}\n AT 测试执行中\n{'='*60}")

        for line in iter(proc.stdout.readline, ""):
            if not line:
                break
            line = line.rstrip("\n")
            stdout_lines.append(line)
            logger.info(line)
            if "oe_test_result:" in line or "The case exit by code" in line:
                cases_done += 1

        proc.wait()
        rc = proc.returncode

        elapsed = time.time() - start_time
        mins, secs = divmod(int(elapsed), 60)
        logger.info(
            f"\n{'='*60}\n✓ AT测试执行完成 [{mins:02d}:{secs:02d}]，"
            f"共 {cases_done} 用例\n{'='*60}"
        )

        stdout = "\n".join(stdout_lines)
        return cmd, rc, stdout, ""

    def _parse_combination_results(self, mugen_dir: str) -> Tuple[int, int, List[str]]:
        results_dir = os.path.join(mugen_dir, "combination_results")
        if not os.path.isdir(results_dir):
            return 0, 0, []

        total = 0
        passed = 0
        failed_cases = []

        for combo_dir_name in os.listdir(results_dir):
            combo_dir = os.path.join(results_dir, combo_dir_name)
            if not os.path.isdir(combo_dir):
                continue
            for suite_dir_name in os.listdir(combo_dir):
                suite_dir = os.path.join(combo_dir, suite_dir_name)
                if not os.path.isdir(suite_dir):
                    continue
                succeed_dir = os.path.join(suite_dir, "succeed")
                failed_dir = os.path.join(suite_dir, "failed")
                if os.path.isdir(succeed_dir):
                    for name in os.listdir(succeed_dir):
                        total += 1
                        passed += 1
                if os.path.isdir(failed_dir):
                    for name in os.listdir(failed_dir):
                        total += 1
                        failed_cases.append(f"{suite_dir_name}/{name}")

        return total, passed, failed_cases

    def _save_execute_log(self, stdout: str, stderr: str, rc: int) -> str:
        log_path = os.path.join(self._evidence_dir, "at_test_execute_log.txt")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("AT 测试执行日志\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"退出码: {rc}\n\n")
            f.write("--- stdout ---\n")
            f.write(stdout if stdout else "(空)")
            f.write("\n\n--- stderr ---\n")
            f.write(stderr if stderr else "(空)")
        return log_path

    def _check_at_tests(self) -> TestResult:
        logger = get_logger()
        result = TestResult(
            category="运行时", sub_item="基础功能",
            requirement="使用 mugen 执行社区 AT 测试用例",
            acceptance_criteria="所有 AT 测试用例结果为 succeed",
        )

        device_cfg = self.config.get("device", {})
        if not device_cfg.get("ip"):
            result.fail_test(detail="未配置目标设备 IP", remediation="请配置 device.ip")
            return result

        mugen_dir = self._ensure_mugen()
        if not mugen_dir:
            result.fail_test(detail="未获取 mugen 测试框架", remediation="请配置 mugen.remote 和 mugen.branch")
            return result

        self._ensure_suite2cases(mugen_dir)

        sdk_path = self._install_sdk()

        config_path = self._prepare_at_config(mugen_dir, sdk_path)
        if not config_path:
            result.fail_test(detail="无法生成 AT 测试配置文件")
            return result

        cmd, rc, stdout, stderr = self._run_at_tests(mugen_dir, config_path)

        log_path = self._save_execute_log(stdout, stderr, rc)
        logger.info(f"AT execute log saved: {log_path}")

        exec_lines = [
            {"text": "# AT 测试执行", "color": "#6c7086"},
            {"text": f"# mugen: {mugen_dir}", "color": "#6c7086"},
            {"text": f"# 设备: {device_cfg.get('user', 'root')}@{device_cfg.get('ip')}", "color": "#6c7086"},
            {"text": "", "color": "#cdd6f4"},
            {"text": f"bash combination.sh -f {os.path.basename(config_path)} -r", "type": "command"},
        ]

        if stdout:
            output_lines = stdout.strip().split("\n")
            tail_lines = output_lines[-15:] if len(output_lines) > 15 else output_lines
            if len(output_lines) > 15:
                exec_lines.append({"text": f"  ... (省略前 {len(output_lines)-15} 行)", "color": "#6c7086"})
            for line in tail_lines:
                if "succeed" in line.lower() or "pass" in line.lower():
                    exec_lines.append({"text": line, "color": "#a6e3a1"})
                elif "fail" in line.lower() or "error" in line.lower():
                    exec_lines.append({"text": line, "color": "#f38ba8"})
                else:
                    exec_lines.append({"text": line, "color": "#6c7086"})

        exec_lines.append({"text": "", "color": "#cdd6f4"})
        exec_lines.append({"text": f"退出码: {rc}", "color": "#89b4fa"})

        path_exec = os.path.join(self._evidence_dir, "at_test_step1_execute.png")
        render_terminal_screenshot("Step 1: AT 测试执行", exec_lines, path_exec)

        total, passed, failed_cases = self._parse_combination_results(mugen_dir)

        if total == 0:
            result.fail_test(
                detail="AT 测试执行完成但未解析到测试结果",
                evidence=f"rc={rc}, screenshot={path_exec}, log={log_path}",
                remediation="请检查 mugen 版本和测试配置",
            )
            return result

        pass_rate = passed / total * 100 if total > 0 else 0

        result_lines = [
            {"text": "# AT 测试结果汇总", "color": "#6c7086"},
            {"text": "", "color": "#cdd6f4"},
            {"text": f"总用例数:   {total}", "color": "#cdd6f4"},
            {"text": f"通过数:     {passed}", "color": "#a6e3a1"},
            {"text": f"失败数:     {len(failed_cases)}", "color": "#f38ba8" if failed_cases else "#a6e3a1"},
            {"text": f"通过率:     {pass_rate:.1f}%", "color": "#f9e2af", "type": "highlight"},
            {"text": "", "color": "#cdd6f4"},
        ]

        if failed_cases:
            result_lines.append({"text": "# 失败用例:", "color": "#6c7086"})
            for fc in failed_cases[:15]:
                result_lines.append({"text": f"  ✗ {fc}", "color": "#f38ba8"})
            if len(failed_cases) > 15:
                result_lines.append({"text": f"  ... (共 {len(failed_cases)} 个失败)", "color": "#6c7086"})
        else:
            result_lines.append({"text": f"所有 {total} 个 AT 用例全部通过", "type": "success"})

        result_lines.append({"text": "", "color": "#cdd6f4"})
        if passed == total:
            result_lines.append({"text": f"AT 测试全部通过: {passed}/{total}", "type": "success"})
        else:
            result_lines.append({"text": f"AT 测试未全部通过: {passed}/{total}", "type": "error"})

        path_result = os.path.join(self._evidence_dir, "at_test_step2_results.png")
        render_terminal_screenshot("Step 2: AT 测试结果", result_lines, path_result)

        if passed == total:
            result.pass_test(
                detail=f"所有 AT 测试用例通过: {passed}/{total}",
                evidence=(
                    f"total: {total}, passed: {passed}, "
                    f"screenshot_exec: {path_exec}, "
                    f"screenshot_result: {path_result}, log: {log_path}"
                ),
            )
        else:
            failed_detail = ", ".join(failed_cases[:10])
            if len(failed_cases) > 10:
                failed_detail += f"... (共 {len(failed_cases)} 个失败)"
            fail_evidence = (
                f"total: {total}, passed: {passed}, "
                f"failed: {len(failed_cases)}, "
                f"screenshot_exec: {path_exec}, "
                f"screenshot_result: {path_result}, log: {log_path}"
            )
            result.fail_test(
                detail=f"AT 测试未全部通过: {passed}/{total}（失败: {failed_detail}）",
                evidence=fail_evidence,
                remediation="请修复失败的 AT 测试用例",
            )

        return result
