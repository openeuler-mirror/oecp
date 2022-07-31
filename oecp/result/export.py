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

import csv
import os
import json
from pathlib import Path

from oecp.proxy.rpm_proxy import RPMProxy
from oecp.result.constants import DETAIL_PATH


def create_csv_report(header, rows, report_path):
    if report_path:
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w', newline='', encoding='utf-8') as f:
            f_csv = csv.DictWriter(f, header)
            f_csv.writeheader()
            f_csv.writerows(rows)
    else:
        return None


def create_directory(root_path, report_name, osv_title, cmp_type=None, uid='', file_format='csv'):
    """
    directory structure
    - reports
        - rpm-provides
            - xxx.rpm_provides.csv
        - rpm-requires
            - xxx.rpm_requires.csv
        ...
    """
    if cmp_type:
        if os.path.exists(root_path):
            first_path = root_path + '/' + osv_title
            if not os.path.exists(first_path):
                os.makedirs(first_path)
            second_path = get_second_path(cmp_type)
            if cmp_type == 'service detail':
                full_second_path = DETAIL_PATH + '/' + second_path
            else:
                full_second_path = first_path + '/' + second_path
            if not os.path.exists(full_second_path):
                os.makedirs(full_second_path)
            if uid:
                report_path = full_second_path + '/' + report_name + '-' + uid + '.' + file_format
            else:
                report_path = full_second_path + '/' + report_name +  '.' + file_format
            return report_path
        else:
            return None
    else:
        if os.path.exists(root_path):
            first_path = root_path + '/' + osv_title
            if not os.path.exists(first_path):
                os.makedirs(first_path)
            report_path = first_path + '/' + report_name + '.' + file_format
            return report_path
        else:
            return None


def get_second_path(cmp_type):
    second_path = ''
    directory_map, all_report_type = read_directory_map()
    if cmp_type in all_report_type:
        for second_path_name in directory_map.keys():
            if cmp_type in directory_map[second_path_name]:
                second_path = second_path_name + '/' + cmp_type.replace(' ', '-')
    else:
        second_path = cmp_type.replace(' ', '-')
    return second_path


def export_json(root_path, report_name, osv_title, result):
    json_report_path = create_directory(root_path, report_name, osv_title, None, '', 'json')
    json_data = json.dumps(result, indent=4, separators=(",", ": "))
    f = open(json_report_path, 'w')
    f.write(json_data)
    f.close


def export_sensitive_results(root_path, result):
    for repo in result:
        for item in repo:
            rpm = item.get('rpm', '')
            kind = item.get('kind', '')
            data = item.get('data', [])
            res = ''
            for diff in data:
                res += f'{diff}\n'
            name = RPMProxy.rpm_name(rpm)
            if res:
                output_path = os.path.join(root_path, kind)
                os.makedirs(output_path, exist_ok=True)
                with open(os.path.join(output_path, f'{name}.txt'), 'w') as f:
                    f.write(res)


def read_directory_map():
    all_report_type = []
    directory_json_path = os.path.join(Path(__file__).parents[1], 'conf', 'directory_structure')
    with open(os.path.join(directory_json_path, 'report_directory_map.json'), 'r') as mf:
        directory_map = json.load(mf)
    for map_key in directory_map.keys():
        all_report_type.extend(directory_map[map_key])
    return directory_map, all_report_type
