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
import logging
import re
import urllib
from urllib.parse import urljoin
from urllib.request import urlopen
import requests
from bs4 import BeautifulSoup

from oecp.main.category import Category
from oecp.proxy.rpm_proxy import RPMProxy
from oecp.main.mapping import SQLiteMapping
from oecp.result.constants import CMP_RESULT_SAME, CMP_RESULT_DIFF, CMP_RESULT_LESS, CMP_RESULT_MORE, \
    CMP_TYPE_RPM_LEVEL, RESULT_LESS, OBSOLETES, PROVIDES, RESULT_MORE, CMP_RESULT_CHANGE, RESULT_DIFF, \
    CMP_RESULT_LINK_CHANGE, CMP_TYPE_SERVICE_DETAIL, CMP_TYPE_RPM_FILES, CMP_TYPE_RPM_PROVIDES, CMP_TYPE_RPM_REQUIRES, \
    CMP_TYPE_RPM_ABI

logger = logging.getLogger("oecp")


def json_result(rows, base_side_a, base_side_b, branch_arch, plan_name):
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
           "more": {
               "more_num": 2,
               "more_details": ["1.rpm", "2.rpm"]
           }
           "diff": {
               "diff_num": 2,
               "diff_details": {
                   "lib_stan": {
                       "name": {
                           "old": xxx,
                           "new": xxx
                        },
                       "rpm_abi":{
                           "diff":{
                               "old": ["a.so_1.0", "b.so_2.0"],
                               "new": ["a.so_1.1", "b.so_2.1"]
                           }
                           "less": [],
                           "more": []
                       },
                       "rpm_provides": {...},
                       "rpm symbol": {
                        "total_effect_other_rpm": [
                            "vala-0.42.2-2.oe1.aarch64.rpm"
                       ...
                   }
               }
           },
           "less": {
               "less_num": 2,
               "less_details": ["3.rpm", "4.rpm"]
           }
           "same": {
               "old": []
               "new": []
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
    pkg_compare_detail.setdefault(CMP_RESULT_MORE, {"more_details": [], "more_num": 0})

    for single_result in rpm_rows:
        if single_result["compare type"] == CMP_TYPE_RPM_LEVEL:
            group_rpm_name_result(pkg_compare_detail, single_result, side_a, side_b, rows, base_side_a, base_side_b)

    if branch_arch and plan_name == "compatibility_influenced":
        check_compatibility_impact(pkg_compare_detail, branch_arch)
    unsame_total = get_unsame_total(pkg_compare_detail)
    compare_result = "not pass" if unsame_total > 0 else "pass"

    return {
        "old": base_side_a,
        "new": base_side_b,
        "compare_result": compare_result,
        "compare_details": pkg_compare_detail
    }


# group by cmp_result
def group_rpm_name_result(detail, single_result, side_a, side_b, rows, base_side_a, base_side_b):
    result = single_result["compare result"]
    rpm_name = single_result.get(side_a) if single_result.get(side_a) else single_result.get(side_b)
    pkg_name = RPMProxy.rpm_name(rpm_name)
    if result in RESULT_LESS:
        rpm_level = get_rpm_level(pkg_name)
        detail[CMP_RESULT_LESS]["less_details"].setdefault(pkg_name, {
            "Name": rpm_name,
            "RPM Level": rpm_level,
            OBSOLETES: "no",
            PROVIDES: "no"
        })
        detail[CMP_RESULT_LESS]["less_num"] += 1
    elif result in RESULT_MORE:
        detail[CMP_RESULT_MORE]["more_details"].append(rpm_name)
        detail[CMP_RESULT_MORE]["more_num"] += 1
    else:
        rpm_result = rows.get(pkg_name)
        ver_change_result = CMP_RESULT_CHANGE if result in RESULT_DIFF else CMP_RESULT_SAME
        rpm_detail, is_same = assign_details(rpm_result, base_side_a, base_side_b, ver_change_result)

        if rpm_detail:
            detail[CMP_RESULT_DIFF]["diff_details"].setdefault(pkg_name, {
                "name": {
                    "old": single_result.get(side_a),
                    "new": single_result.get(side_b)
                },
                "version": ver_change_result
            })
            detail[CMP_RESULT_DIFF]["diff_details"][pkg_name].update(rpm_detail)

        if is_same:
            detail[CMP_RESULT_SAME]["same_details"]["old"].append(single_result.get(side_a))
            detail[CMP_RESULT_SAME]["same_details"]["new"].append(single_result.get(side_b))
            detail[CMP_RESULT_SAME]["same_num"] += 1
        else:
            detail[CMP_RESULT_DIFF]["diff_num"] += 1


def get_rpm_level(rpm_name):
    level_map = {
        0: "level0",
        1: "level1",
        2: "level2",
        3: "level3"
    }
    rpm_level = Category().category_of_bin_package(rpm_name)

    return level_map.get(rpm_level.value, "level4")


def assign_details(rpm_result, base_side_a, base_side_b, ver_result):
    diff_detail = {}
    is_same = True if ver_result == CMP_RESULT_SAME else False
    if not rpm_result:
        return diff_detail, is_same

    for cmp_type, results in rpm_result.items():
        single_cmp_result = {}
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
                if result == CMP_RESULT_MORE and cmp_type in [CMP_TYPE_SERVICE_DETAIL, CMP_TYPE_RPM_FILES]:
                    continue
                else:
                    is_same = False
        if single_cmp_result:
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
        if cmp_type == "version" and cmp_results == CMP_RESULT_CHANGE:
            changed_result = False
        elif cmp_type in [CMP_TYPE_RPM_FILES, CMP_TYPE_RPM_PROVIDES]:
            if cmp_results.get(CMP_RESULT_LESS):
                changed_result = False
        elif cmp_type == CMP_TYPE_RPM_REQUIRES:
            if cmp_results.get(CMP_RESULT_MORE) or cmp_results.get(CMP_RESULT_LESS):
                changed_result = False
        elif cmp_type == CMP_TYPE_RPM_ABI:
            if cmp_results.get(CMP_RESULT_DIFF) or cmp_results.get(CMP_RESULT_LESS):
                changed_result = False

    return changed_result


def get_repodata_sqlite(url):
    sqlite_path = ""
    suffix = "primary.sqlite.bz2"
    try:
        with urlopen(url) as u:
            html = u.read().decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            links = soup.find_all('a')
    except urllib.error.HTTPError as err:
        logger.warning(f"Get primary sqlite url error: {url}, {err}")
        return sqlite_path
    sqlite_name = [link.get('href') for link in links if link.get('href').endswith(suffix)]
    if not sqlite_name:
        logger.warning(f"Not find primary sqlite, url: {url}")
    sqlite_path = urljoin(url, sqlite_name[0])

    return sqlite_path


def get_sqlite_url(branch_arch):
    sqlite_urls = {}
    openeuler_repo = "https://repo.openeuler.org/"
    match_result = re.match("(.+)?-(.+)", branch_arch)
    if not match_result:
        logger.warning("Please input correct args --branch-arch, eg: 22.03-LTS-SP1-x86_64")
        return sqlite_urls
    base_branch = match_result.group(1)
    branch = "openEuler-" + base_branch if not base_branch.startswith('openEuler') else base_branch
    arch = match_result.group(2)
    if base_branch.split('-')[-1] in ["20.09", "21.03", "21.09", "22.09"]:
        openeuler_repo = "https://repo.huaweicloud.com/openeuler/"
    for repo in ["everything", "EPOL"]:
        last_repodata = f"{branch}/{repo}/{arch}/repodata/"
        url = urljoin(openeuler_repo, last_repodata)
        response = requests.head(url)
        if response.status_code == 404:
            last_repodata = f"{branch}/{repo}/main/{arch}/repodata/"
            url = urljoin(openeuler_repo, last_repodata)
        sqlite_path = get_repodata_sqlite(url)
        if sqlite_path:
            sqlite_urls.setdefault(repo, sqlite_path)

    return sqlite_urls


def query_database_provides(diff_details, sqlite_urls):
    '''
    rpm_provides eg:

    {
        "log4j": {
            "mvn(log4j:log4j)": {
                "symbol": "EQ",
                "epoch": "0",
                "version": "2.17.2",
                "release" None
            }
        },
            ......
    }
    '''
    rpm_provides = {}
    everything_sqlite_url = sqlite_urls.get("everything", "")
    epol_sqlite_url = sqlite_urls.get("EPOL", "")
    everything_sqlite_obj = SQLiteMapping(everything_sqlite_url) if everything_sqlite_url else None
    epol_sqlite_obj = SQLiteMapping(epol_sqlite_url) if epol_sqlite_url else None
    for rpm, check_result in diff_details.items():
        if is_compatibility(check_result):
            continue

        query_provides = {}
        if everything_sqlite_url:
            query_provides = everything_sqlite_obj.get_rpm_provides(rpm)
        if not query_provides and epol_sqlite_url:
            query_provides = epol_sqlite_obj.get_rpm_provides(rpm, database="EPOL")
        rpm_provides.setdefault(rpm, query_provides)

    return rpm_provides


def check_compatibility_impact(pkg_compare_detail, branch_arch):
    diff_details = pkg_compare_detail.get("diff", {}).get("diff_details", {})
    result_urls = get_sqlite_url(branch_arch)
    if result_urls:
        rpm_provides = query_database_provides(diff_details, result_urls)
        for repo_url in result_urls.values():
            if not repo_url:
                continue
            sqlite_obj = SQLiteMapping(repo_url, log=False)
            for rpm, provides in rpm_provides.items():
                diff_details.get(rpm).setdefault("probably compatible influence", [])
                repo_impact = sqlite_obj.get_direct_require_rpms(provides)
                diff_details.get(rpm).get("probably compatible influence").extend(repo_impact)
    else:
        logger.warning(
            "Please input correct arg --branch-arch, eg:(openEuler-22.03-LTS-SP1-x86_64/22.03-LTS-SP1-x86_64)")
