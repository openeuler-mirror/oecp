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
import json
import logging
import os.path
import re

from oecp.main.category import Category
from oecp.main.mapping import SQLiteMapping
from oecp.result.constants import *
from oecp.proxy.rpm_proxy import RPMProxy

logger = logging.getLogger("oecp")


def json_result(rows, base_side_a, base_side_b):
    """
    :param rows:
    :param base_side_a:
    :param base_side_b:
    :return:
    {
        "old": xxxx,
        "new": xxxx,
        "compare_result": "not pass",
        "compare_details": {
            "same": {
                "same_details": {
                    "old": []
                    "new": []
               },
               "same_num": 0
           },
            "diff": {
                "diff_details": {
                    "lib_stan": {
                        "name": {
                            "old": xxx,
                            "new": xxx
                        },
                        "RPM Level": "level4",
                        "rpm_abi": {
                            "diff": {
                                "old": ["a.so_1.0", "b.so_2.0"],
                                "new": ["a.so_1.1", "b.so_2.1"]
                            },
                            "less": [],
                            "more": []
                        },
                        "rpm_provides": {},
                        "rpm_config": {},
                        "rpm symbol": {
                            "total_effect_other_rpm": [
                                "vala-0.42.2-2.oe1.aarch64.rpm"
                                ...
                            ]
                        }
                    }
                },
                "diff_num": 1
            },
            "less": {
                "less_details": {
                    "hisi_zip": {
                        "Name": "hisi_zip-1.3.10-5.oe1.aarch64.rpm",
                        "RPM Level": "level4",
                        "Obsoletes": "no",
                        "Provides": "no"
                    }
                },
                "less_num": 1
            },
            "more": {
                "more_details": {
                    "hisi_sec2": {
                        "Name": "hisi_sec2-1.3.10-6.oe2003sp4.aarch64.rpm",
                        "RPM Level": "level4"
                    }
                },
                "more_num": 1
            }
        }
    }
    """
    side_a = get_binary_side(base_side_a)
    side_b = get_binary_side(base_side_b)
    pkg_compare_detail = {}
    rpm_rows = rows['rpm']
    del rows['rpm']
    rows = simplify_key(rows)
    pkg_compare_detail.setdefault(CMP_RESULT_SAME, {
        "same_details": {
            "old": [],
            "new": []
        },
        "same_num": 0
    })
    pkg_compare_detail.setdefault(CMP_RESULT_DIFF, {"diff_details": {}, "diff_num": 0})
    pkg_compare_detail.setdefault(CMP_RESULT_LESS, {"less_details": {}, "less_num": 0})
    pkg_compare_detail.setdefault(CMP_RESULT_MORE, {"more_details": {}, "more_num": 0})

    for single_result in rpm_rows:
        if single_result["compare type"] == CMP_TYPE_RPM_LEVEL:
            group_rpm_name_result(pkg_compare_detail, single_result, side_a, side_b, rows, base_side_a, base_side_b)

    unsame_total = get_unsame_total(pkg_compare_detail)
    compare_result = "not pass" if unsame_total > 0 else "pass"

    return {
        "old": base_side_a,
        "new": base_side_b,
        "compare_result": compare_result,
        "compare_details": pkg_compare_detail
    }


# group by cmp_result
def group_rpm_name_result(pkg_compare_detail, single_result, side_a, side_b, rows, base_side_a, base_side_b):
    result = single_result["compare result"]
    rpm_name = single_result.get(side_a) if single_result.get(side_a) else single_result.get(side_b)
    pkg_name = RPMProxy.rpm_name(rpm_name)
    if result in RESULT_LESS:
        rpm_level = get_rpm_level(pkg_name)
        pkg_compare_detail[CMP_RESULT_LESS]["less_details"].setdefault(pkg_name, {
            "Name": rpm_name,
            "RPM Level": rpm_level,
            OBSOLETES: "no",
            PROVIDES: "no"
        })
        pkg_compare_detail[CMP_RESULT_LESS]["less_num"] += 1
    elif result in RESULT_MORE:
        rpm_level = get_rpm_level(pkg_name)
        pkg_compare_detail[CMP_RESULT_MORE]["more_details"].setdefault(pkg_name, {
            "Name": rpm_name,
            "RPM Level": rpm_level
        })
        pkg_compare_detail[CMP_RESULT_MORE]["more_num"] += 1
    else:
        rpm_result = rows.get(pkg_name)
        rpm_detail, is_same = assign_details(rpm_result, base_side_a, base_side_b, pkg_name, result)
        if rpm_detail:
            pkg_compare_detail[CMP_RESULT_DIFF]["diff_details"].setdefault(pkg_name, {
                "name": {
                    "old": single_result.get(side_a),
                    "new": single_result.get(side_b)
                },
                "RPM Level": get_rpm_level(pkg_name)
            })
            pkg_compare_detail[CMP_RESULT_DIFF]["diff_details"][pkg_name].update(rpm_detail)
        if is_same:
            pkg_compare_detail[CMP_RESULT_SAME]["same_details"]["old"].append(single_result.get(side_a))
            pkg_compare_detail[CMP_RESULT_SAME]["same_details"]["new"].append(single_result.get(side_b))
            pkg_compare_detail[CMP_RESULT_SAME]["same_num"] += 1
        else:
            pkg_compare_detail[CMP_RESULT_DIFF]["diff_num"] += 1


def get_rpm_level(rpm_name):
    level_map = {
        0: "level0",
        1: "level1",
        2: "level2",
        3: "level3"
    }
    rpm_level = Category().category_of_bin_package(rpm_name)

    return level_map.get(rpm_level.value, "level4")


def assign_details(rpm_result, base_side_a, base_side_b, pkg_name, result):
    diff_detail = {}
    is_same = False if result in RESULT_DIFF else True
    if not rpm_result:
        return diff_detail, is_same
    for cmp_type, results in rpm_result.items():
        single_cmp_result = {}
        if cmp_type in [CMP_TYPE_RPM, CMP_TYPE_SERVICE_DETAIL]:
            continue

        if cmp_type == CMP_TYPE_RPM_SYMBOL:
            effect_rpm = []
            for single_result in results:
                result = single_result["compare result"]
                if result == CMP_RESULT_SAME:
                    continue
                single_cmp_result.setdefault(result, [])
                old_file = single_result.get(base_side_a)
                new_file = single_result.get(base_side_b)
                abi_detail = single_result.get('abi details', {})
                effect_rpm.extend(abi_detail.get("effect_rpm", []))
                single_cmp_result[result].append({'old': old_file, 'new': new_file, 'details': abi_detail})
                is_same = False
            effect_rpm = list(set(effect_rpm))
            for rpm in effect_rpm:
                if pkg_name == RPMProxy.rpm_name(rpm):
                    effect_rpm.remove(rpm)
            if effect_rpm:
                single_cmp_result.setdefault("total_effect_other_rpm", effect_rpm)
        else:
            for single_result in results:
                result = single_result["compare result"]
                if result in [CMP_RESULT_SAME, CMP_RESULT_CHANGE]:
                    continue
                elif result in [CMP_RESULT_DIFF, CMP_RESULT_LINK_CHANGE]:
                    single_cmp_result.setdefault(result, {
                        "old": [],
                        "new": []
                    })
                    single_cmp_result[result]["old"].append(single_result.get(base_side_a))
                    single_cmp_result[result]["new"].append(single_result.get(base_side_b))
                    is_same = False
                else:
                    obj = single_result.get(base_side_a) if single_result.get(base_side_a) else single_result.get(
                        base_side_b)
                    single_cmp_result.setdefault(result, [])
                    single_cmp_result[result].append(obj)
                    if result == CMP_RESULT_MORE and cmp_type == CMP_TYPE_RPM_FILES:
                        continue
                    else:
                        is_same = False

        diff_detail.setdefault(cmp_type, single_cmp_result)

    return diff_detail, is_same


def get_binary_side(side):
    return side + " binary rpm package"


def simplify_key(rows):
    if not rows:
        return {}

    new_rows = {}
    for k, v in rows.items():
        if k.endswith(".rpm") and not k.endswith(".src.rpm"):
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


def is_compatibility(single_check_result):
    changed_result = True
    for cmp_type, cmp_results in single_check_result.items():
        if cmp_type == CMP_TYPE_NAME:
            _, old_ver = RPMProxy.rpm_name_version(cmp_results.get("old"))
            _, new_ver = RPMProxy.rpm_name_version(cmp_results.get("new"))
            if old_ver != new_ver:
                changed_result = False
        elif cmp_type in [CMP_TYPE_RPM_FILES, CMP_TYPE_RPM_PROVIDES]:
            if cmp_results.get(CMP_RESULT_LESS):
                changed_result = False
        elif cmp_type == CMP_TYPE_RPM_REQUIRES:
            if cmp_results.get(CMP_RESULT_MORE) or cmp_results.get(CMP_RESULT_LESS):
                changed_result = False

    return changed_result


def get_sqlite_url(branch_arch):
    openeuler_repo = "https://repo.huaweicloud.com/openeuler/"
    match_result = re.match("(.+)?-(.+)", branch_arch)
    if not match_result:
        logger.warning("Not get os branch name and arch info, please input correct arg --branch-arch")
        return []
    branch, arch = "openEuler-" + match_result.group(1), match_result.group(2)
    sqlite_branch_conf = os.path.join(os.path.realpath(os.path.dirname(os.path.dirname(__file__))),
                                      "conf/sqlite_branch/sqlite_of_branch.json")
    with open(sqlite_branch_conf, "r") as f:
        map_sqlite_branch = json.load(f)
    sqlite_urls = map_sqlite_branch.get(branch, {}).get(arch)
    if not sqlite_urls:
        logger.warning(f"the branch name: {branch} or arch: {arch} not in openeuler sqlite of branch.")
        return []

    result_urls = [os.path.join(openeuler_repo, branch, repo, url) for repo, url in sqlite_urls.items()]

    return result_urls


def query_database_provides(diff_details, result_urls):
    rpm_provides = {}
    sqlite_obj = SQLiteMapping(result_urls[0])
    for rpm, check_result in diff_details.items():
        if is_compatibility(check_result):
            continue

        query_provides = sqlite_obj.get_rpm_provides(rpm)
        rpm_provides.setdefault(rpm, query_provides)

    sqlite_obj = SQLiteMapping(result_urls[1])
    for rpm, provides in rpm_provides.items():
        if not provides:
            query_provides = sqlite_obj.get_rpm_provides(rpm, database="EPOL")
            rpm_provides.get(rpm).extend(query_provides)

    return rpm_provides


def check_compatibility_impact(pkg_compare_detail, branch_arch):
    diff_details = pkg_compare_detail.get("diff", {}).get("diff_details", {})
    result_urls = get_sqlite_url(branch_arch)
    if result_urls:
        rpm_provides = query_database_provides(diff_details, result_urls)
        for repo_url in result_urls:
            sqlite_obj = SQLiteMapping(repo_url, log=False)
            for rpm, provides in rpm_provides.items():
                diff_details.get(rpm).setdefault("probably compatible influence", [])
                repo_impact = sqlite_obj.get_direct_require_rpms(provides)
                diff_details.get(rpm).get("probably compatible influence").extend(repo_impact)
