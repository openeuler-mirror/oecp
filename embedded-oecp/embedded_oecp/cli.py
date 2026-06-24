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
import argparse
import os
import sys
import yaml
from embedded_oecp.utils.config import (
    load_config, ensure_workdir,
)
from embedded_oecp.utils.logger import setup_logger, get_logger
from embedded_oecp.runner import TestRunner, resolve_checkers
from embedded_oecp.models import TEST_ITEMS, TestStatus, TestResult
from embedded_oecp.report.generator import ReportGenerator


def build_parser():
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="openEuler Embedded OSV 兼容性认证测试工具",
    )
    parser.add_argument("-c", "--config", default=None, help="配置文件路径（覆盖 workdir/conf/config.yaml）")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("-d", "--image-build-dir", default=None, dest="image_build_dir",
                        help="镜像编译目录（构建工程根目录）")
    parser.add_argument("--device-ip", default=None, dest="device_ip", help="目标设备 IP 地址")
    parser.add_argument("--device-user", default=None, dest="device_user", help="目标设备用户名")
    parser.add_argument("--device-password", default=None, dest="device_password", help="目标设备密码")
    parser.add_argument("--arch", default=None, dest="arch", help="目标架构: aarch64/arm32/x86_64/riscv64")
    parser.add_argument("--toolchain-dir", default=None, dest="toolchain_dir",
                        help="工具链目录（如 /usr1/openeuler/gcc/openeuler_gcc_arm64le）")
    parser.add_argument("--build-timestamp", default=None, dest="build_timestamp",
                        help="镜像编译时间戳（如 2026-05-19_20:30:00）")
    parser.add_argument("--sdk-file", default=None, dest="sdk_file",
                        help="镜像 SDK 文件路径（用于计算文件名和 MD5）")

    sub = parser.add_subparsers(dest="command", help="子命令")

    run_parser = sub.add_parser("run", help="执行测试")
    run_parser.add_argument(
        "-p", "--plan",
        default="all",
        help=(
            "测试计划 (默认: all)\n"
            "  大类:\n"
            "    all       - 全部检测项\n"
            "    source    - 源码认证 (内核/基础中间件/其他软件包)\n"
            "    build     - 构建认证 (编译链/构建工程/包列表)\n"
            "    runtime   - 运行时认证 (C库运行时/基础功能AT/POSIX)\n"
            "  具体测试项:\n"
            "    source: kernel, middleware, package\n"
            "    build:  compiler, project, pkglist\n"
            "    runtime: libc_runtime, at_test, posix"
        ),
    )
    run_parser.add_argument("--no-cache", action="store_true", dest="no_cache", help="忽略缓存，强制重新执行")

    cache_parser = sub.add_parser("cache", help="缓存管理")
    cache_parser.add_argument("action", choices=["clear", "list"], help="clear: 清理缓存, list: 列出缓存状态")
    cache_parser.add_argument("-p", "--plan", default=None, dest="plan", help="指定测试项（不指定则操作全部）")

    sub.add_parser("summary", help="测试结果汇总")
    sub.add_parser("report", help="生成认证报告")
    sub.add_parser("list", help="列出所有测试项")

    save_parser = sub.add_parser("save", help="将命令行参数写入配置文件")
    save_parser.add_argument("-o", "--output", default=None, dest="output", help="输出路径（默认覆盖 workdir/conf/config.yaml）")

    return parser


def cmd_list():
    logger = get_logger()
    logger.info(f"{'大类':<10} {'测试项':<20} {'子项':<12} {'说明'}")
    logger.info("-" * 70)
    for group_name, items in TEST_ITEMS.items():
        for item_name, meta in items.items():
            logger.info(
                f"{group_name:<10} {item_name:<20} "
                f"{meta['sub_item']:<12} {meta['display']}"
            )


def cmd_run(args, config):
    setup_logger(verbose=config.get("verbose", False) or args.verbose)
    logger = get_logger()
    runner = TestRunner(config)
    results = runner.run(plan=args.plan, force=args.no_cache)

    logger.info(f"\n{'='*60}")
    logger.info(f"{'测试项':<25} {'状态':<8} {'说明'}")
    logger.info("-" * 60)
    for r in results:
        logger.info(f"{r.sub_item:<25} {r.status:<8} {r.detail[:40]}")
    logger.info(f"{'='*60}")

    passed = sum(1 for r in results if r.status == TestStatus.PASS.value)
    failed = sum(1 for r in results if r.status == TestStatus.FAIL.value)
    none = sum(1 for r in results if r.status == TestStatus.NONE.value)
    logger.info(f"PASS: {passed}  FAIL: {failed}  NONE: {none}")


def cmd_summary(config):
    setup_logger(verbose=config.get("verbose", False))
    logger = get_logger()
    runner = TestRunner(config)
    results = runner.summary()
    conclusion = runner.conclusion()

    logger.info(f"\n{'='*70}")
    logger.info(f"{'项目':<8} {'子项':<14} {'要求':<20} {'状态':<8} {'说明'}")
    logger.info("-" * 70)
    for r in results:
        logger.info(
            f"{r.category:<8} {r.sub_item:<14} "
            f"{r.requirement:<20} {r.status:<8} {r.detail[:30]}"
        )
    logger.info(f"{'='*70}")
    logger.info(f"\n认证结论: {conclusion}")


def cmd_report(config):
    setup_logger(verbose=config.get("verbose", False))
    runner = TestRunner(config)

    all_cached = runner.cache.load_all()
    raw_results = []
    for checker_name, cached_list in all_cached.items():
        for item in cached_list:
            raw_results.append(TestResult(
                category=item.get("category", ""),
                sub_item=item.get("sub_item", ""),
                requirement=item.get("requirement", ""),
                acceptance_criteria=item.get("acceptance_criteria", ""),
                status=item.get("status", "NONE"),
                detail=item.get("detail", ""),
                evidence=item.get("evidence", ""),
                remediation=item.get("remediation", ""),
            ))

    conclusion = runner.conclusion()
    generator = ReportGenerator(output_dir=config.get("output_dir", "/tmp/embedded-oecp/report"))
    generator.generate(raw_results, conclusion, config=config)
    logger = get_logger()
    logger.info(f"Report generated in {config.get('output_dir')}")


def cmd_cache(args, config):
    logger = get_logger()
    from embedded_oecp.cache import ResultCache
    work_dir = config.get("work_dir", "/tmp/embedded-oecp")
    cache = ResultCache(work_dir)

    if args.action == "list":
        all_cached = cache.load_all()
        if not all_cached:
            logger.info("无缓存数据")
            return

        display_map = {}
        for group_name, items in TEST_ITEMS.items():
            for item_name, meta in items.items():
                display_map[item_name] = meta

        checker_names = []
        for group in TEST_ITEMS.values():
            checker_names.extend(group.keys())

        ordered = [n for n in checker_names if n in all_cached]
        for name in sorted(all_cached.keys()):
            if name not in ordered:
                ordered.append(name)

        for name in ordered:
            items = all_cached[name]
            if not items:
                continue

            meta = display_map.get(name, {})
            category = meta.get("category", items[0].get("category", ""))
            if hasattr(category, "value"):
                category = category.value
            sub_item = meta.get("sub_item", items[0].get("sub_item", ""))
            display = meta.get("display", name)

            passed = sum(1 for it in items if it.get("status") == TestStatus.PASS.value)
            failed = sum(1 for it in items if it.get("status") == TestStatus.FAIL.value)
            total = len(items)

            if failed > 0:
                overall = TestStatus.FAIL.value
            elif passed == total:
                overall = TestStatus.PASS.value
            else:
                overall = TestStatus.NONE.value

            status_mark = {"PASS": "✓", "FAIL": "✗", "NONE": "○"}.get(overall, "○")

            logger.info(f"{status_mark} {name} ({category}/{sub_item})  {overall}  [{passed}/{total} 通过]")
            logger.info(f"  {display}")
            for it in items:
                st = it.get("status", TestStatus.NONE.value)
                detail = it.get("detail", "")
                tag = {"PASS": "[PASS]", "FAIL": "[FAIL]", "NONE": "[NONE]"}.get(st, f"[{st}]")
                logger.info(f"  {tag} {detail}")
            logger.info("")

    elif args.action == "clear":
        if args.plan:
            names = resolve_checkers(args.plan) if args.plan in ("all", "source", "build", "runtime") else [args.plan]
        else:
            names = None
        cache.clear(names)
        if names:
            logger.info(f"已清理缓存: {', '.join(names)}")
        else:
            logger.info("已清理全部缓存")


def _save_config(args, config: dict, workspace: str):
    save_path = getattr(args, "output", None)
    if not save_path:
        save_path = os.path.join(workspace, "conf", "config.yaml")
    save_path = os.path.abspath(save_path)
    save_data = {}

    for key in ("baseline_repo", "baseline_branch", "verbose", "arch"):
        if config.get(key) is not None:
            save_data[key] = config[key]

    for section in ("kernel", "image_build", "toolchain", "device", "mugen"):
        val = config.get(section)
        if val and isinstance(val, dict):
            filtered = {k: v for k, v in val.items() if v is not None}
            if filtered:
                save_data[section] = filtered

    for key in ("build_timestamp", "sdk_file"):
        if config.get(key):
            save_data[key] = config[key]

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "w", encoding="utf-8") as f:
        yaml.dump(save_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    logger = get_logger()
    logger.info(f"配置已保存到: {save_path}")


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    workspace = ensure_workdir()
    config = load_config(args.config, workspace=workspace)

    if args.image_build_dir:
        abs_dir = os.path.abspath(args.image_build_dir)
        config.setdefault("image_build", {})["dir"] = abs_dir
        if not config.get("toolchain", {}).get("dir"):
            toolchain_subdir = os.path.join(abs_dir, "gcc")
            if os.path.isdir(toolchain_subdir):
                config.setdefault("toolchain", {})["dir"] = toolchain_subdir

    if args.device_ip:
        config.setdefault("device", {})["ip"] = args.device_ip
    if args.device_user:
        config.setdefault("device", {})["user"] = args.device_user
    if args.device_password:
        config.setdefault("device", {})["password"] = args.device_password
    if args.arch:
        config["arch"] = args.arch
    if getattr(args, "toolchain_dir", None):
        config.setdefault("toolchain", {})["dir"] = os.path.abspath(args.toolchain_dir)
    if getattr(args, "build_timestamp", None):
        config["build_timestamp"] = args.build_timestamp
    if getattr(args, "sdk_file", None):
        sdk_path = os.path.abspath(args.sdk_file)
        config["sdk_file"] = sdk_path

    if args.command == "run":
        cmd_run(args, config)
    elif args.command == "summary":
        cmd_summary(config)
    elif args.command == "report":
        cmd_report(config)
    elif args.command == "list":
        cmd_list()
    elif args.command == "cache":
        cmd_cache(args, config)
    elif args.command == "save":
        _save_config(args, config, workspace)


if __name__ == "__main__":
    main()
