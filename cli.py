# -*- encoding=utf-8 -*-
"""
# **********************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# [oecp] is licensed under the Mulan PSL v1.
# You can use this software according to the terms and conditions of the Mulan PSL v1.
# You may obtain a copy of Mulan PSL v1 at:
#     http://license.coscl.org.cn/MulanPSL
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v1 for more details.
# Author:
# Create: 2021-09-07
# Description: from markdown to json
# **********************************************************************************
"""
import os
import sys
import logging
import argparse

from oecp.result.compress import compress_report
from oecp.result.constants import CMP_TYPE_SYMBOL, BRANCH_NAME, DB_PASSWORD, BASE_SIDE, OSV_SIDE
from oecp.utils.logger import init_logger
from oecp.main.plan import Plan
from oecp.symbol_analyze.analyze import RpmAnalyze


def init_args():
    """
    init args
    :return:
    """
    parser = argparse.ArgumentParser()

    default_conf_path = os.path.join(os.path.dirname(__file__), "oecp/conf")
    default_plan_path = os.path.join(default_conf_path, "plan/daily_symbol.json")
    default_perf_baseline_file = os.path.join(
        default_conf_path, "performance/baseline-openEuler-20.03-LTS-SP1-everything-aarch64-dvd.iso.performance.json")
    default_work_dir = "/tmp/oecp"
    default_output_file = "/tmp/oecp/"

    parser.add_argument("-v", "--version", action='version', version='oecp 1.0')
    parser.add_argument("-d", "--debuginfo", help="read compare files from plan json", action='store_true')
    parser.add_argument("-n", "--parallel", type=int, dest="parallel", help="compare parallel, in order if 0")
    parser.add_argument("-w", "--work-dir", type=str, dest="work_dir", default=default_work_dir, help="work root dir")
    parser.add_argument("-p", "--plan", type=str, dest="plan_path", default=default_plan_path, help="compare plan path")
    parser.add_argument("-b", "--baseline", type=str, dest="perf_baseline_file", default=default_perf_baseline_file,
                        help="baseline performance result")

    parser.add_argument("-f", "--format", type=str, dest="output_format", default="json", help="result export format")
    parser.add_argument("-o", "--output", type=str, dest="output_file", default=default_output_file,
                        help="result output path")

    parser.add_argument("compare_files", metavar="file", type=str, nargs='*', help="compare files")
    parser.add_argument("--check", help="check the file's result", type=str, dest="check_result")
    parser.add_argument("--submit", help="submit job to compass-ci", type=str, dest="submit", default='at')

    parser.add_argument("-s", "--symbol", type=str, dest="symbol", help="rpm is influenced by changing symbol")
    parser.add_argument("--pull-request-id", type=str, dest="pr_id", help="pull-request-id")
    parser.add_argument("--submit-symbol", dest="submit_symbol", action='store_true')
    parser.add_argument("--branch-arch", type=str, dest="branch_arch",
                        help="os branch name and arch, eg: 22.03-LTS-SP1-x86_64")
    parser.add_argument("--spec", type=str, dest="spec_dir", help="spec file directory path")

    parser.add_argument("--db-password", type=str, dest="databse_password", help="the password of symbol database")
    parser.set_defaults(func=do_compress)

    return parser.parse_args()


def do_compress(report_dir, params):
    compress_report(report_dir, params.output_file)


if __name__ == "__main__":
    init_logger()
    logger = logging.getLogger("oecp")

    args = init_args()
    logger.info(f"--plan: {args.plan_path}")
    logger.info(f"--baseline: {args.perf_baseline_file}")
    logger.info(f"--work_dir: {args.work_dir}")
    logger.info(f"--format: {args.output_format}")
    logger.info(f"--output: {args.output_file}")
    logger.info(f"--symbol: {args.symbol}")
    logger.info(f"--pull-request-id: {args.pr_id}")
    logger.info(f"--spec: {args.spec_dir}")

    from oecp.main.factory import Factory

    # 门禁pr合入，更新数据库symbol信息
    if args.submit_symbol:
        RpmAnalyze(args, repository_old=None, repository_new=None).submit_symbol_change()
        sys.exit(0)
    product_a, product_b = None, None
    if args.symbol:
        cmp_files_num = len(args.compare_files)
        plan_base_name = os.path.basename(args.plan_path)

        # 提交包升级pr，查询symbol影响的rpm包，构建临时表信息
        if CMP_TYPE_SYMBOL in plan_base_name and cmp_files_num == 2:
            product_a = Factory.create(args.compare_files[0], args, "none", BASE_SIDE)
            product_b = Factory.create(args.compare_files[1], args, "none", OSV_SIDE)
            is_tmp_table = True
        # 构建symbol全量数据库
        elif cmp_files_num == 1:
            product_b = Factory.create(args.compare_files[0], args, "none", BASE_SIDE)
            is_tmp_table = False
        else:
            logger.error("The command input is incorrect.")
            raise ValueError("The command input is incorrect.")

        if product_b:
            RpmAnalyze(args, repository_old=product_a, repository_new=product_b).construct_database(is_tmp_table)
            logger.info("Construct database success!")
        else:
            logger.error("RPM package not found, please check the directory you entered.")

        if not is_tmp_table:
            sys.exit(0)
    branch_arch = args.branch_arch if args.branch_arch else args.symbol
    plan = Plan(args.plan_path, args.output_file, branch_arch)
    if args.parallel is not None:
        plan.parallel = args.parallel
    logger.info(f"--parallel: {plan.parallel}")

    _ = not os.path.exists(args.work_dir) and os.mkdir(args.work_dir)
    _ = not os.path.exists(args.output_file) and os.mkdir(args.output_file)

    if args.debuginfo:
        logger.info(f"start compare {plan.get_base()} with {plan.get_other()}")
        product_a = Factory.create(plan.get_base(), args, plan.get_type(), BASE_SIDE)
        product_b = Factory.create(plan.get_other(), args, plan.get_type(), OSV_SIDE)
    else:
        cmp_files_num = len(args.compare_files)
        if cmp_files_num != 2:
            logger.error(f"The compare files are {args.compare_files}")
            logger.error(f"The number of input compare files is {cmp_files_num}, but need 2")
            sys.exit(1)
        logger.info(f"start compare {args.compare_files[0]} with {args.compare_files[1]}")
        product_a = product_a if product_a else Factory.create(args.compare_files[0], args, "none", BASE_SIDE)
        product_b = product_b if product_b else Factory.create(args.compare_files[1], args, "none", OSV_SIDE)
        if args.symbol:
            plan.config_of(CMP_TYPE_SYMBOL)[BRANCH_NAME] = args.symbol
            plan.config_of(CMP_TYPE_SYMBOL)[DB_PASSWORD] = args.databse_password
    for side, dir_repository in enumerate([product_a, product_b]):
        if not dir_repository:
            logger.error(f"Please check {args.compare_files[side]} does not contain the focus on rpm packages.")
            sys.exit(1)
    result = product_a.compare(product_b, plan)
    args_use = (args.output_file, args.output_format, args.compare_files[1], args.spec_dir, args.branch_arch,
                plan.plan_name)
    osv_title = result.export(*args_use)
    args.func(osv_title, args)
