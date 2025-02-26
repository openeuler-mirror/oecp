# -*- encoding=utf-8 -*-
"""
# **********************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# [oecp] is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
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
from oecp.result.constants import BASE_SIDE, OSV_SIDE
from oecp.utils.logger import init_logger
from oecp.main.plan import Plan


def init_args():
    """
    init args
    :return:
    """
    parser = argparse.ArgumentParser()

    default_conf_path = os.path.join(os.path.dirname(__file__), "oecp/conf")
    default_plan_path = os.path.join(default_conf_path, "plan/all.json")
    default_category_path = os.path.join(default_conf_path, "category/category.json")
    default_work_dir = "/tmp/oecp"
    default_output_file = "/tmp/oecp/"

    parser.add_argument("-v", "--version", action='version', version='oecp 1.0')
    parser.add_argument("-d", "--debuginfo", help="read compare files from plan json", action='store_true')
    parser.add_argument("-n", "--parallel", type=int, dest="parallel", help="compare parallel, in order if 0")
    parser.add_argument("-w", "--work-dir", type=str, dest="work_dir", default=default_work_dir, help="work root dir")
    parser.add_argument("-p", "--plan", type=str, dest="plan_path", default=default_plan_path, help="compare plan path")
    parser.add_argument("-c", "--category", type=str, dest="category_path", default=default_category_path,
                        help="package category path")
    parser.add_argument("-f", "--format", type=str, dest="output_format", default="csv", help="result export format")
    parser.add_argument("-o", "--output", type=str, dest="output_file", default=default_output_file,
                        help="result output path")
    parser.add_argument("-b", "--branch", type=str, dest="branch", default="20.03-LTS-SP1",
                        help="compare base branch name")
    parser.add_argument("-a", "--arch", type=str, dest="arch", default="aarch64", help="compare arch")
    parser.add_argument("-s", "--src_kernel", type=str, dest="src_kpath", default=os.path.dirname(__file__),
                        help="src kernel path")
    parser.add_argument("--platform", type=str, dest="platform_test", default=default_output_file,
                        help="platform test json result path")
    parser.add_argument("compare_files", metavar="file", type=str, nargs='*', help="compare files")
    parser.add_argument("--submit", help="submit job to compass-ci", type=str, dest="submit", default='at')
    parser.add_argument("-r", "--rpm-name", type=str, dest="rpm_name", help="name of file belong to rpm")
    parser.set_defaults(func=do_compress)
    return parser.parse_args()


def do_compress(report_dir, params):
    compress_report(report_dir, params.output_file)


if __name__ == "__main__":
    init_logger()
    logger = logging.getLogger("oecp")

    args = init_args()
    logger.info(f"--plan: {args.plan_path}")
    logger.info(f"--category: {args.category_path}")
    logger.info(f"--platform: {args.platform_test}")
    logger.info(f"--work_dir: {args.work_dir}")
    logger.info(f"--format: {args.output_format}")
    logger.info(f"--output: {args.output_file}")

    plan = Plan(args)
    if args.parallel is not None:
        plan.parallel = args.parallel
    logger.info(f"--parallel: {plan.parallel}")

    _ = not os.path.exists(args.work_dir) and os.mkdir(args.work_dir)
    _ = not os.path.exists(args.output_file) and os.mkdir(args.output_file)

    from oecp.main.factory import Factory
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
        product_a = Factory.create(args.compare_files[0], args, "none", BASE_SIDE)
        product_b = Factory.create(args.compare_files[1], args, "none", OSV_SIDE)

    result = product_a.compare(product_b, plan)
    e_args = (args.output_file, args.output_format, args.compare_files, args.platform_test)
    osv_title = result.export(*e_args)
    args.func(osv_title, args)
