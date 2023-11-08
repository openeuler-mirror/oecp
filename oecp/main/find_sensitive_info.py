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
import logging
import argparse

CURR_DIR = os.path.dirname(__file__)
PRJ_PATH = os.path.abspath(os.path.join(CURR_DIR, '..', '..'))
if PRJ_PATH not in os.sys.path:
    os.sys.path.insert(0, PRJ_PATH)

from oecp.utils.logger import init_logger
from oecp.main.plan import Plan
from oecp.result.export import export_sensitive_results

def init_args():
    """
    init args
    :return:
    """
    parser = argparse.ArgumentParser()

    default_conf_path = os.path.join(PRJ_PATH, "oecp/conf")
    default_plan_path = os.path.join(default_conf_path, "plan/sensitive_info.json")
    default_category_path = os.path.join(default_conf_path, "category/category.json")
    default_perf_baseline_file = os.path.join(default_conf_path, "performance/baseline-openEuler-20.03-LTS-SP1-everything-aarch64-dvd.iso.performance.json")
    default_work_dir = "/tmp/oecp"
    default_output_file = "/tmp/oecp/"
    
    parser.add_argument("-n", "--parallel", type=int, dest="parallel", help="compare parallel, in order if 0")
    parser.add_argument("-w", "--work-dir", type=str, dest="work_dir", default=default_work_dir, help="work root dir")
    parser.add_argument("-p", "--plan", type=str, dest="plan_path", default=default_plan_path, help="compare plan path")
    parser.add_argument("-c", "--category", type=str, dest="category_path", default=default_category_path, help="package category path")
    parser.add_argument("-b", "--baseline", type=str, dest="perf_baseline_file", default=default_perf_baseline_file, help="baseline performance result")
    parser.add_argument("-a", "--arch", type=str, dest="architecture", default="x86_64", choices=["x86_64", "aarch64"], help="repo arch")
    parser.add_argument("-f", "--format", type=str, dest="output_format", default="csv", help="result export format")
    parser.add_argument("-o", "--output", type=str, dest="output_file", default=default_output_file, help="result output path")
    parser.add_argument("compare_files", metavar="file", type=str, nargs=1, help="compare files")

    return parser.parse_args()


def find_sensitive_info():
    """
    find sensitive info, string and image
    :return:
    """
    init_logger()
    logger = logging.getLogger("oecp")

    args = init_args()
    logger.info(f"start analysis {args.compare_files[0]}")
    logger.info(f"--plan: {args.plan_path}")
    logger.info(f"--category: {args.category_path}")
    logger.info(f"--baseline: {args.perf_baseline_file}")
    logger.info(f"--work_dir: {args.work_dir}")
    logger.info(f"--arch: {args.architecture}")
    logger.info(f"--format: {args.output_format}")
    logger.info(f"--output: {args.output_file}")
    
    plan = Plan(args.plan_path)
    if args.parallel is not None:
        plan.parallel = args.parallel
    logger.info(f"--parallel: {plan.parallel}")

    _ = not os.path.exists(args.work_dir) and os.mkdir(args.work_dir)
    _ = not os.path.exists(args.output_file) and os.mkdir(args.output_file)

    from oecp.main.factory import Factory
    product_a = Factory.create(args.compare_files[0], args, plan.get_type())
    results = []
    if hasattr(product_a, 'find_sensitive_str'):
        result = product_a.find_sensitive_str(plan)
        results += result
    if hasattr(product_a, 'find_sensitive_image'):
        result = product_a.find_sensitive_image(plan)
        results += result
    export_sensitive_results(args.output_file, results)


def _main():    
    find_sensitive_info()


if __name__ == "__main__":
    _main()
