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
# Create: 2021-12-9
# Description: json result
# **********************************************************************************
"""

from oecp.proxy.rpm_proxy import RPMProxy
from oecp.result.constants import CMP_TYPE_RPM_LEVEL, RESULT_DIFF, RESULT_LESS, CMP_RESULT_LESS, RESULT_MORE, \
    CMP_RESULT_MORE, CMP_RESULT_SAME, CMP_RESULT_DIFF, CMP_TYPE_RPM_REQUIRES, RESULT_SAME


# -------------------------------------------------------------------------------
# json result
# {
#   "old_path": xxxx,
#   "new_path": xxxx,
#   "compare_result": "not pass",
#   "compare_details": {
#       "more": {
#           "more_num": 2,
#           "more_details": ["1.rpm", "2.rpm"]
#       }
#       "diff": {
#           "diff_num": 2,
#           "diff_details": {
#               "lib_stan": {
#                   "name": {
#                       "old": xxx,
#                       "new": xxx
#                    },
#                   "rpm_abi":{
#                       "diff":{
#                           "old": ["a.so_1.0", "b.so_2.0"],
#                           "new": ["a.so_1.1", "b.so_2.1"]
#                       }
#                       "less": [],
#                       "more": []
#                   }
#                   "rpm_provides": {...}
#                   ...
#               }
#           }
#       },
#       "less": {
#           "less_num": 2,
#           "less_details": ["3.rpm", "4.rpm"]
#       }
#       "same": {
#           "old": []
#           "new": []
#       }
#   }
# }
# -------------------------------------------------------------------------------
def json_result(rows, base_side_a, base_side_b):
    side_a = get_binary_side(base_side_a)
    side_b = get_binary_side(base_side_b)
    pkg_compare_detail = {}
    rpm_rows = rows['rpm']
    del rows['rpm']
    rows = simplify_key(rows)

    for single_result in rpm_rows:
        if single_result["compare type"] == CMP_TYPE_RPM_LEVEL:
            args = (pkg_compare_detail, single_result, side_a, side_b, rows, base_side_a, base_side_b)
            group_rpm_name_result(*args)

    unsame_total = get_unsame_total(pkg_compare_detail)
    compare_result = "not pass" if unsame_total > 0 else "pass"

    return {
        "old": base_side_a,
        "new": base_side_b,
        "compare_result": compare_result,
        "compare_details": pkg_compare_detail
    }


# group by cmp_result
def group_rpm_name_result(*args):
    detail, single_result, side_a, side_b, rows, base_side_a, base_side_b = args
    result = single_result["compare result"]
    rpm_name = single_result.get(side_b) if single_result.get(side_b) else single_result.get(side_a)
    pkg_name = RPMProxy.rpm_name(rpm_name)
    if rows.get(pkg_name):
        detail_args = (detail, single_result, side_a, side_b, rows, pkg_name)
        detail_setdefault(*detail_args)
    if result in RESULT_DIFF:
        assign_diff_details(detail, pkg_name, base_side_a, base_side_b, rows.get(pkg_name))
    elif result in RESULT_LESS:
        detail[CMP_RESULT_LESS]["less_details"].append(rpm_name)
        detail[CMP_RESULT_LESS]["less_num"] += 1
    elif result in RESULT_MORE:
        detail[CMP_RESULT_MORE]["more_details"].append(rpm_name)
        detail[CMP_RESULT_MORE]["more_num"] += 1
    else:
        rpm_result = rows.get(pkg_name)
        if is_same(rpm_result):
            detail[CMP_RESULT_SAME]["same_details"]["old"].append(single_result.get(side_a))
            detail[CMP_RESULT_SAME]["same_details"]["new"].append(single_result.get(side_b))
            detail[CMP_RESULT_SAME]["same_num"] += 1
        else:
            assign_diff_details(detail, pkg_name, base_side_a, base_side_b, rpm_result)


def detail_setdefault(*detail_args):
    detail, single_result, side_a, side_b, rows, pkg_name = detail_args
    detail.setdefault(CMP_RESULT_SAME, {
        "same_details": {
            "old": [],
            "new": []
        },
        "same_num": 0
    })
    detail.setdefault(CMP_RESULT_DIFF, {"diff_details": {}, "diff_num": 0})
    detail[CMP_RESULT_DIFF]["diff_details"].setdefault(pkg_name, {
        "name": {
            "old": single_result.get(side_a),
            "new": single_result.get(side_b)
        }
    })
    for cmp_type in rows.get(pkg_name):
        detail[CMP_RESULT_DIFF]["diff_details"][pkg_name].setdefault(cmp_type, {})
    detail.setdefault(CMP_RESULT_LESS, {"less_details": [], "less_num": 0})
    detail.setdefault(CMP_RESULT_MORE, {"more_details": [], "more_num": 0})


def assign_diff_details(detail, pkg_name, base_side_a, base_side_b, rpm_result):
    detail[CMP_RESULT_DIFF]["diff_num"] += 1
    rpm_detail = assign_details(rpm_result, base_side_a, base_side_b)
    if rpm_detail:
        detail[CMP_RESULT_DIFF]["diff_details"][pkg_name].update(rpm_detail)


def assign_details(rpm_result, base_side_a, base_side_b):
    if not rpm_result:
        return None
    diff_detail = {}
    for cmp_type, results in rpm_result.items():
        diff_detail.setdefault(cmp_type, {})
        for single_result in results:
            result = single_result["compare result"]
            if result == "same":
                continue

            if cmp_type == CMP_TYPE_RPM_REQUIRES:
                side_a = base_side_a + " symbol name"
                side_b = base_side_b + " symbol name"
                obj = single_result.get(side_a) if single_result.get(side_a) else single_result.get(side_b)
                diff_detail[cmp_type].setdefault(result, [])
                diff_detail[cmp_type][result].append(obj)
            else:
                if result in RESULT_DIFF:
                    diff_detail.get(cmp_type).setdefault(result, {
                        "old": [],
                        "new": []
                    })
                    diff_detail.get(cmp_type).get(result)["old"].append(single_result.get(base_side_a))
                    diff_detail.get(cmp_type).get(result)["new"].append(single_result.get(base_side_b))
                else:
                    obj = single_result.get(base_side_a) if single_result.get(base_side_a) else single_result.get(
                        base_side_b)
                    diff_detail[cmp_type].setdefault(result, [])
                    diff_detail[cmp_type][result].append(obj)

    return diff_detail


def get_binary_side(side):
    return side + " binary rpm package"


def simplify_key(rows):
    if not rows:
        return None

    new_rows = {}
    for k, v in rows.items():
        if not k.endswith(".src.rpm"):
            new_rows[RPMProxy.rpm_name(k)] = v
    return new_rows


def get_unsame_total(compare_detail):
    total = 0
    for result_type, detail in compare_detail.items():
        if result_type == CMP_RESULT_SAME:
            continue
        num = result_type + "_num"
        total += detail[num]

    return total


def is_same(rpm_cmp_result):
    for cmp_type, result in rpm_cmp_result.items():
        for row in result:
            if row.get("compare result") not in RESULT_SAME:
                return False
    return True
