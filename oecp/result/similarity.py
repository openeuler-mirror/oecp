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
# Create: 2021-10-15
# Description: similarity
# **********************************************************************************
"""
import logging
import os

from oecp.result.constants import CMP_TYPE_RPM_LEVEL, CMP_TYPE_RPMS_TEST, CMP_TYPE_RPM, SIMILARITY_TYPES, \
    CMP_TYPE_CI_CONFIG, CMP_TYPE_AT, CMP_TYPE_PERFORMANCE, CMP_TYPE_RPM_ABI, RESULT_SAME, PKG_SIMILARITY_SON_TYPES, \
    CMP_TYPE_RPM_FILES, CMP_RESULT_MORE
from oecp.result.test_result import get_perf_reg, load_json_result, small_better

logger = logging.getLogger("oecp")

PKG_NAME = {
    '1': "same",
    '1.1': "same",
    '2': "same",
    '3': "diff",
    '4': "less",
    '5': "more"
}


def get_similarity(rows, side_a, side_b):
    similarity = {}
    count = {}
    count[CMP_TYPE_RPM_LEVEL], _ = rpm_count(rows, side_a, side_b)
    count[CMP_TYPE_RPMS_TEST] = rpm_test_count(rows.get(CMP_TYPE_RPM))

    for node, results in rows.items():
        if not isinstance(results, list):
            for rpm_type, rpm_results in results.items():
                if rpm_type in SIMILARITY_TYPES:
                    for result in rpm_results:
                        count_single_result(count, result, rpm_type)

    level1_name_rate = count_rate(count[CMP_TYPE_RPM_LEVEL][1]["same"],
                                  (count[CMP_TYPE_RPM_LEVEL][1]["same"] + count[CMP_TYPE_RPM_LEVEL][1]["diff"]))
    level2_same = count[CMP_TYPE_RPM_LEVEL][1]["same"] + count[CMP_TYPE_RPM_LEVEL][2]["same"]
    level2_diff = count[CMP_TYPE_RPM_LEVEL][1]["diff"] + count[CMP_TYPE_RPM_LEVEL][2]["diff"]
    leve2_name_rate = count_rate(level2_same, (level2_same + level2_diff))
    core_pkg_rate = count_rate(count[CMP_TYPE_RPM_LEVEL]["core_pkg"]["same"],
                               count[CMP_TYPE_RPM_LEVEL]["core_pkg"]["same"] + count[CMP_TYPE_RPM_LEVEL]["core_pkg"][
                                   "diff"])
    similarity["core_pkg"] = core_pkg_rate
    similarity["level1 pkg"] = level1_name_rate
    similarity["level2 pkg"] = leve2_name_rate
    similarity["all_pkg"] = get_all_pkg_simlarity(count[CMP_TYPE_RPM_LEVEL])
    del count[CMP_TYPE_RPM_LEVEL]

    rmp_test_score = count_rate(count[CMP_TYPE_RPMS_TEST]["same"],
                                (count[CMP_TYPE_RPMS_TEST]["same"] + count[CMP_TYPE_RPMS_TEST]["diff"]))
    similarity[CMP_TYPE_RPMS_TEST] = rmp_test_score
    del count[CMP_TYPE_RPMS_TEST]

    count[CMP_TYPE_CI_CONFIG] = ci_test_count(rows.get(CMP_TYPE_CI_CONFIG), "same")
    similarity[CMP_TYPE_CI_CONFIG] = count_rate(count[CMP_TYPE_CI_CONFIG]["same"],
                                                (count[CMP_TYPE_CI_CONFIG]["same"] + count[CMP_TYPE_CI_CONFIG]["diff"]))
    del count[CMP_TYPE_CI_CONFIG]

    count[CMP_TYPE_AT] = ci_test_count(rows.get(CMP_TYPE_AT), "pass")
    similarity[CMP_TYPE_AT] = count_rate(count[CMP_TYPE_AT]["same"],
                                         count[CMP_TYPE_AT]["same"] + count[CMP_TYPE_AT]["diff"])
    del count[CMP_TYPE_AT]

    similarity[CMP_TYPE_PERFORMANCE] = performance_rate(rows.get(CMP_TYPE_PERFORMANCE), side_b)

    for count_type, result in count.items():
        if count_type == CMP_TYPE_RPM_ABI:
            l1_rate = count_rate(count[count_type][1]["same"],
                                 (count[count_type][1]["same"] + count[count_type][1]["diff"]))
            l2_same = count[count_type][1]["same"] + count[count_type][2]["same"]
            l2_diff = count[count_type][1]["diff"] + count[count_type][2]["diff"]
            l2_rate = count_rate(l2_same, l2_same + l2_diff)
            similarity["level1 " + count_type] = l1_rate
            similarity["level2 " + count_type] = l2_rate
        rate = count_rate(count[count_type]["all"]["same"],
                          (count[count_type]["all"]["same"] + count[count_type]["all"]["diff"]))
        similarity[count_type] = rate
    return similarity


def get_all_pkg_simlarity(count):
    same = 0
    diff = 0
    for level, result in count.items():
        if level == "core_pkg":
            continue
        same += result["same"]
        diff += result["diff"]

    return count_rate(same, same + diff)


def count_single_result(count, result, cmp_type):
    count.setdefault(cmp_type, {
        1: {"same": 0, "diff": 0},
        2: {"same": 0, "diff": 0},
        'all': {"same": 0, "diff": 0},
    })
    if cmp_type == CMP_TYPE_RPM_ABI:
        category_level = result.get("category level", 6)
        if category_level < 3:
            if result["compare result"] in RESULT_SAME:
                count[cmp_type][category_level]['same'] += 1
            else:
                count[cmp_type][category_level]['diff'] += 1
    if result["compare result"] in RESULT_SAME:
        count[cmp_type]['all']['same'] += 1
    else:
        count[cmp_type]['all']['diff'] += 1


def rpm_count(rows, side_a, side_b):
    rpm_results = rows.get(CMP_TYPE_RPM)
    count = {
        1: {"same": 0, "diff": 0},
        2: {"same": 0, "diff": 0},
        3: {"same": 0, "diff": 0},
        4: {"same": 0, "diff": 0},
        "core_pkg": {"same": 0, "diff": 0}
    }
    mark_pkgs = []
    if not rpm_results:
        return count, mark_pkgs

    for result in rpm_results:
        if not result["compare type"] == CMP_TYPE_RPM_LEVEL:
            continue

        pkg = result[side_a + " binary rpm package"]

        if float(result["compare result"]) > 4:
            continue

        if result["category level"] == 0:
            if float(result["compare result"]) > 2:
                b = result.get(side_b + " binary rpm package")
                mark_pkg = b if b else pkg
                mark_pkgs.append(mark_pkg)
                count["core_pkg"]["diff"] += 1
            else:
                if is_same_rpm(rows.get(pkg)):
                    count["core_pkg"]["same"] += 1
                else:
                    count["core_pkg"]["diff"] += 1
        else:
            if (result["compare result"] in RESULT_SAME) and is_same_rpm(rows.get(pkg)):
                count[result["category level"]]["same"] += 1
            else:
                count[result["category level"]]["diff"] += 1
    return count, mark_pkgs


def is_same_rpm(rpm_cmp_result):
    if not rpm_cmp_result:
        return True
    for cmp_type, result in rpm_cmp_result.items():
        if cmp_type not in PKG_SIMILARITY_SON_TYPES:
            continue
        for row in result:
            if row.get("compare type") == CMP_TYPE_RPM_FILES and row.get("compare result") == CMP_RESULT_MORE:
                continue
            if row.get("compare result") not in RESULT_SAME:
                return False
    return True


def rpm_test_count(results):
    count = {
        "same": 0,
        "diff": 0
    }
    if not results:
        return count
    for result in results:
        if not result["compare type"] == CMP_TYPE_RPMS_TEST:
            continue
        if result["compare result"] == "same":
            count["same"] += 1
        if result["compare result"] == "diff":
            count["diff"] += 1
    return count


def ci_test_count(result_rows, pass_result):
    count = {
        "same": 0,
        "diff": 0
    }
    if not result_rows:
        return count
    for result in result_rows:
        if result["compare result"] == pass_result:
            count["same"] += 1
        else:
            count["diff"] += 1
    return count


# weight:
#   lmbench3.*  : 15%
#   unixbench.* : 50%
#   mysql.*:      35%
def performance_rate(results, side_b):
    weight = {
        'lmbench3': 0.15,
        'unixbench': 0.5,
        'mysql': 0.35
    }
    rate = 0
    perf_count = perfomance_count(results, side_b)
    for test, count in perf_count.items():
        if count:
            test_rate = sum(count) / len(count) * weight[test]
            rate += test_rate

    return rate


def perfomance_count(results, side_b):
    count = {
        'lmbench3': [],
        'unixbench': [],
        'mysql': []
    }
    if not results:
        return count
    small_better_reg = get_perf_reg()['small_better']
    perf_reg_path = os.path.join(os.path.dirname(__file__), "../conf/performance/perf-reg.json")
    perf_reg = load_json_result(perf_reg_path)
    perf_filter = tuple(perf_reg['filter'])

    for result in results:
        metric = result['metric']
        if metric in perf_filter:
            if not result[side_b]:
                msg = side_b + " missed the performance test: " + result['metric']
                logger.warning(msg)
                continue
            side_b_result = result[side_b]
            baseline_result = result['baseline']
            cmp_result = result['compare result']
            score = 0
            if small_better(metric, small_better_reg):
                if cmp_result == 'pass':
                    score = (baseline_result - side_b_result) / baseline_result + 1
                else:
                    score = 1 - (side_b_result - baseline_result) / baseline_result
            else:
                score = side_b_result / baseline_result
            if 'lmbench3' in metric:
                count['lmbench3'].append(score)
            elif 'unixbench' in metric:
                count['unixbench'].append(score)
            else:
                count['mysql'].append(score)
    return count


def count_rate(a, b):
    rate = 0
    if b:
        rate = round(a / b, 4)

    return rate
