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
# Create: 2021-09-06
# Description: compare plan
# **********************************************************************************
"""

CASE_START_TEXT = "start to run"
CASE_END_TEXT = "End to run"
END_TEXT = "A total of"
CASE_EXIT_CODE = "The case exit by code"


def parse_case_name(log_text):
    if len(log_text) != 3:
        return ''
    case_name_start = log_text[0].strip('.').split(CASE_START_TEXT)[-1].strip().split(':')[-1]
    case_name_end = log_text[2].strip('.').split(CASE_END_TEXT)[-1].strip().split(':')[-1]
    case_status = log_text[1].strip('.').split()[-1]
    if not case_name_start or not case_name_end:
        return ''
    if case_name_start == case_name_end:
        if case_status == '0': 
            return f'{case_name_start}.pass'
        else: 
            return f'{case_name_start}.fail'

    return ''


def parse_result(result_path):
    log_text = ['', '', '']
    result = {}
    with open(result_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if CASE_START_TEXT in line:
                log_text[0] = line
            if CASE_EXIT_CODE in line:
                log_text[1] = line
            if CASE_END_TEXT in line:
                log_text[2] = line
                result[parse_case_name(log_text)] = 1
                log_text = ['', '', '']
    return result
