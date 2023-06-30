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
# Create: 2021-09-08
# Description: compare result
# **********************************************************************************
"""
import os
import json
import logging

from oecp.result.constants import CMP_RESULT_SAME, CMP_TYPE_CI_FILE_CONFIG, CMP_TYPE_CI_CONFIG, CMP_RESULT_MORE, \
    CMP_RESULT_LESS, CMP_RESULT_DIFF, CMP_TYPE_RPMS_TEST

logger = logging.getLogger("oecp")


# ------------------------------------------------------------------------------------
# parse compass-ci test result for export csv report
# requires:
#   - performacne: 2 performace test result at least in root_path(the platform test result path)
#     eg:
#        openEuler-20.03-LTS-aarch64-dvd.iso.performance.json
#        openEuler-20.03-LTS-SP1-aarch64-dvd.iso.performance.json
#
#   - rpm tests: 2 cmds+services test result at least in root_path
#     eg:
#        openEuler-20.03-LTS-aarch64-dvd.iso.tests.json
#        openEuler-20.03-LTS-SP1-aarch64-dvd.iso.tests.json
#   - AT: 1 test result at least in root_path
#       eg: EulixOS-Server-1.0-aarch64.iso.at.json
# ------------------------------------------------------------------------------------

def performance_result_parser(side_a, side_b, root_path):
    perf_result = []
    side_b_result = get_performacnce_result(side_b, root_path)
    if not side_b_result:
        logger.warning("not exists target performance json file.")

        return perf_result

    side_a_result = get_performacnce_result(side_a, root_path)
    if not side_a_result:
        base_path = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))
        base_performance = os.path.join(base_path, "conf/performance/baseline-openEuler-20.03-LTS-SP1-everything"
                                                   "-aarch64-dvd.iso.performance.json")
        side_a_result = load_json_result(base_performance)

    for metric, value in side_a_result.items():
        avg_b = side_b_result.get(metric, {}).get('average')
        baseline_avg, cmp_result = cmp_performance_metric(metric, value, avg_b)
        row = {
            "metric": metric,
            side_a: side_a_result[metric]['average'] if side_a_result.get(metric) else '',
            side_b: avg_b,
            "baseline": baseline_avg,
            "compare result": cmp_result
        }
        perf_result.append(row)

    return perf_result


def cmp_performance_metric(metric, value, avg_b):
    """
    lmbench性能测试指标项结果与基线平均值比较计算
    @param metric: 测试指标项
    @param value: 基线文件性能测试指标项均值
    @param avg_b: osv性能测试指标项均值
    @return: baseline_avg（区分延迟指标测试项与其它指标项），cmp_result（比较结果）
    """
    small_better_reg = get_perf_reg()['small_better']
    if small_better(metric, small_better_reg):
        baseline_avg = value['average'] + (value['average'] * 0.05)
        if avg_b:
            cmp_result = 'pass' if avg_b - baseline_avg < 0 else 'fail'
        else:
            cmp_result = ''
    else:
        baseline_avg = value['average'] - (value['average'] * 0.05)
        if avg_b:
            cmp_result = 'fail' if avg_b - baseline_avg < 0 else 'pass'
        else:
            cmp_result = ''

    return baseline_avg, cmp_result


def get_performacnce_result(side, root_path):
    # find the result of side in root_path
    file_name = side + '.performance.json'
    result_path = os.path.join(root_path, file_name)

    return load_json_result(result_path)


# -------------------------------------------------------------------------
# parse etc config json file
def ciconfig_result_parser(side_a, side_b, root_path):
    ciconfig_result = []
    config_file_result = []
    side_a_result = get_ciconfig_result(side_a, root_path)
    side_b_result = get_ciconfig_result(side_b, root_path)
    if not side_a_result or not side_b_result:
        logger.warning("json file not exist")
        return ciconfig_result, config_file_result
    commons = side_a_result.keys() & side_b_result.keys()
    mores = side_a_result.keys() - side_b_result.keys()
    less = side_b_result.keys() - side_a_result.keys()
    for filename in commons:
        file_row = {
            side_a: os.path.basename(filename),
            side_b: os.path.basename(filename),
            "compare result": CMP_RESULT_SAME,
            "sidea path": side_a_result[filename]['path'],
            "sideb path": side_b_result[filename]['path'],
            "compare type": CMP_TYPE_CI_FILE_CONFIG
        }
        config_file_result.append(file_row)
        all_detail = format_ciconfig_detail(side_a_result[filename]['data'], side_b_result[filename]['data'])
        for component_result in all_detail:
            for sub_component_result in component_result:
                row = {
                    side_a: sub_component_result[0],
                    side_b: sub_component_result[1],
                    "compare result": sub_component_result[2],
                    "file name": os.path.basename(filename),
                    "compare type": CMP_TYPE_CI_CONFIG
                }
                ciconfig_result.append(row)
    for filename in mores:
        file_row = {
            side_a: os.path.basename(filename),
            side_b: '',
            "compare result": CMP_RESULT_MORE,
            "sidea path": side_a_result[filename]['path'],
            "sideb path": '',
            "compare type": CMP_TYPE_CI_FILE_CONFIG
        }
        config_file_result.append(file_row)
    for filename in less:
        file_row = {
            side_a: '',
            side_b: os.path.basename(filename),
            "compare result": CMP_RESULT_LESS,
            "sidea path": '',
            "sideb path": side_b_result[filename]['path'],
            "compare type": CMP_TYPE_CI_FILE_CONFIG
        }
        config_file_result.append(file_row)
    return ciconfig_result, config_file_result


def get_ciconfig_result(side, root_path):
    file_name = side + '.ciconfig.json'
    result_path = os.path.join(root_path, file_name)
    return load_json_result(result_path)


def format_ciconfig_detail(data_a, data_b):
    same = []
    changed = []
    losted = []
    all_dump = []
    for k, va in data_a.items():
        vb = data_b.get(k, None)
        if vb is None:
            losted.append([' '.join([k, "=", va]), '', CMP_RESULT_MORE])
        elif va == vb:
            same.append([' '.join([k, "=", va]), ' '.join([k, "=", vb]), CMP_RESULT_SAME])
        else:
            changed.append([' '.join([k, "=", va]), ' '.join([k, "=", vb]), CMP_RESULT_DIFF])
    all_dump.append(same)
    all_dump.append(changed)
    all_dump.append(losted)
    return all_dump


def small_better(metric, small_better_reg):
    for i in small_better_reg:
        if i in metric:
            return True

    return False


def get_perf_reg():
    perf_reg_path = os.path.join(os.path.dirname(__file__), "../conf/performance/perf-reg.json")
    return load_json_result(perf_reg_path)


# ------------------------------------------------------------------------
# parse the test result which includes: rpm-cmds and rpm service
def test_result_parser(side_a, side_b, root_path):
    dump_a = get_test_result(side_a, root_path)
    dump_b = get_test_result(side_b, root_path)

    if dump_b and dump_a:
        category_map = create_category_map()
        return assain_rpm_test_result(side_a, side_b, dump_a, dump_b, category_map)
    else:
        return [], {}


def assgin_rpm_summay(rpm_test_details, side_a, side_b):
    summary = {}
    fail_rows = []
    for rpm, rpm_result in rpm_test_details.items():
        values = rpm_result[CMP_TYPE_RPMS_TEST]
        assgin_fail_test_row(values, fail_rows, side_a, side_b)
        rpm_side_result = {
            side_a: "pass",
            side_b: "pass"
        }
        level = ''
        for v in values:
            level = v.get("category level") if v.get("category level") else "6"
            summary.setdefault(level, {
                "category level": level,
                "[success] " + side_a: 0,
                "[fail] " + side_a: 0,
                "[success] " + side_b: 0,
                "[fail] " + side_b: 0,
            })
            for side in [side_a, side_b]:
                if v[side].endswith("fail"):
                    rpm_side_result[side] = "fail"
        for s, result in rpm_side_result.items():
            if result == "fail":
                summary.get(level)["[fail] " + s] += 1
            else:
                summary.get(level)["[success] " + s] += 1
    return sorted(summary.values(), key=lambda i: i["category level"]) + fail_rows


def assgin_fail_test_row(results, fail_rows, side_a, side_b):
    row = {}
    for result in results:
        if result[side_a].endswith("fail") or result[side_b].endswith("fail"):
            row = {
                "category level": result['category level'],
                "[success] " + side_a: '',
                "[fail] " + side_a: '',
                "[success] " + side_b: '',
                "[fail] " + side_b: '',
            }
            for side in [side_a, side_b]:
                if result[side].endswith("fail"):
                    row["[fail] " + side] = result['binary rpm package']
    if row:
        fail_rows.append(row)


def assain_rpm_test_result(side_a, side_b, dump_a, dump_b, category_map):
    rpm_test_rows = []
    rpm_test_details = {}
    a_keys = dump_a.keys()
    b_keys = dump_b.keys()
    keys = list(set(a_keys).union(set(b_keys)))
    for key in keys:
        va = dump_a.get(key, {})
        vb = dump_b.get(key, {})

        src_side = va.get('rpm_src_name') if va else vb.get('rpm_src_name')
        category_level = category_map.get(src_side, 'level6')[-1]

        defatule_side_a = key if va else ''
        rpm_side_a = va.get('rpm_full_name', defatule_side_a)
        rpm_side_b = vb.get('rpm_full_name', defatule_side_a)

        defatule_side_b = key if vb else ''
        src_side_a = va.get('rpm_src_name', defatule_side_b)
        src_side_b = vb.get('rpm_src_name', defatule_side_b)

        remove_useless_result(va, vb)
        rpm_pkg = key
        rpm_cmp_result = compare(va, vb)
        rpm_test_details.setdefault(rpm_pkg, {})
        rpm_test_details.get(rpm_pkg)[CMP_TYPE_RPMS_TEST] = assain_rpm_test_details(rpm_pkg, side_a, side_b, va, vb,
                                                                                    category_level)

        row = {
            side_a + " binary rpm package": rpm_side_a,
            side_a + " source package": src_side_a,
            side_b + " binary rpm package": rpm_side_b,
            side_b + " source package": src_side_b,
            "compare result": rpm_cmp_result,
            "compare detail": ' ' + CMP_TYPE_RPMS_TEST.replace(' ', '-') + '/' + key + '.csv ',
            "compare type": CMP_TYPE_RPMS_TEST,
            "category level": category_level
        }
        rpm_test_rows.append(row)

    return rpm_test_rows, rpm_test_details


def assain_rpm_test_details(rpm_pkg, side_a, side_b, dump_a, dump_b, level):
    rows = []
    dump_a = format_test_detail(dump_a)
    dump_b = format_test_detail(dump_b)

    a_keys = dump_a.keys() if dump_a else ''
    b_keys = dump_b.keys() if dump_b else ''
    keys = list(set(a_keys).union(set(b_keys)))

    for key in keys:
        va = key + ': ' + dump_a.get(key) if dump_a and dump_a.get(key) else ''
        vb = key + ': ' + dump_b.get(key) if dump_b and dump_b.get(key) else ''
        row = {
            "binary rpm package": rpm_pkg,
            side_a: va,
            side_b: vb,
            "compare result": compare(va, vb),
            "compare type": CMP_TYPE_RPMS_TEST,
            "category level": level
        }
        rows.append(row)
    return rows


def remove_useless_result(va, vb):
    for k in ['rpm_src_name', 'rpm_full_name']:
        if va.get(k):
            va.pop(k)
        if vb.get(k):
            vb.pop(k)


def format_test_detail(result):
    '''
    :param: result
        eg: {
                "install": "pass"
	        "cmds": {
                    "/usr/bin/dockerd": "pass",
                    "/usr/bin/runc": "pass",
                    "/usr/bin/docker": "pass"
                },
        ...
	    }
    '''
    if not result:
        return ''
    new_result = {}
    for k, v in result.items():
        parse_dump(k, v, new_result)
    return new_result


def parse_dump(key, value, new_result):
    if isinstance(value, dict):
        for k, v in value.items():
            parse_dump(key + '.' + k, v, new_result)
    else:
        new_result[key] = value


def compare(a, b):
    if a == b:
        return CMP_RESULT_SAME
    elif a and (not b):
        return CMP_RESULT_LESS
    elif b and (not a):
        return CMP_RESULT_MORE
    else:
        return CMP_RESULT_DIFF


def get_test_result(side, root_path):
    file_name = side + '.tests.json'
    result_path = os.path.join(root_path, file_name)

    return load_json_result(result_path)


def load_json_result(result_path):
    try:
        if not os.path.exists(result_path):
            logger.warning(f"{result_path} not exist")
            return None
        with open(result_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"{os.path.realpath(result_path)} not exist")
        return None


def create_category_map():
    category_map = {}
    category_file = os.path.join(os.path.dirname(__file__), "../conf/category/category.json")
    categorys = load_json_result(category_file)
    for category in categorys:
        category_map[category['src']] = category['level']

    return category_map


# ------------------------------------------------------------------------
# parse the AT result
NON_AT_RESULT = {
    "osv-smoke.osv_smoke_nr_total",
    "osv-smoke.osv_smoke_nr_pass",
    "osv-smoke.osv_smoke_nr_fail"
}


def at_result_parser(side_b, root_path):
    at_result = []
    side_b_result = get_at_result(side_b, root_path)
    if not side_b_result:
        return []

    for metric, _ in side_b_result.items():
        if metric in NON_AT_RESULT:
            continue

        values = metric.split('.')
        test_name = values[1]
        result = values[2]
        row = {
            side_b: test_name,
            'compare result': result
        }
        at_result.append(row)
    return at_result


def get_at_result(side, root_path):
    file_name = side + '.at.json'
    result_path = os.path.join(root_path, file_name)

    return load_json_result(result_path)
