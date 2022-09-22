# -*- encoding=utf-8 -*-
"""
# **********************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# [oecp] is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v1.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author:
# Create: 2021-09-06
# Description: compare result
# **********************************************************************************
"""
# COMPARE_RESULT
CMP_RESULT_MORE = "more"
CMP_RESULT_LESS = "less"
CMP_RESULT_DIFF = "diff"
CMP_RESULT_SAME = "same"
CMP_RESULT_CHANGE = "change"
CMP_RESULT_EXCEPTION = "exception"
CMP_RESULT_TO_BE_DETERMINED = "to be determined"

# COMPARE_TYPE
CMP_TYPE_PLAIN = "plain"
CMP_TYPE_EXECUTABLE = "executable"
CMP_TYPE_DYNAMIC_LIBRARY = "dynamic library"
CMP_TYPE_STRUCTURED = "structured"
CMP_TYPE_ZIP = "zip"
CMP_TYPE_NULL = "null"
CMP_TYPE_JAR = "jar"
CMP_TYPE_WAR = "war"
CMP_TYPE_GZIP = "gzip"
CMP_TYPE_RPM = "rpm"
CMP_TYPE_RPM_KERNEL = "kernel"
CMP_TYPE_DIRECTORY = "repository directory"
CMP_TYPE_ISO = "iso"
CMP_TYPE_DIST_REPOSITORY = "dist repository"
CMP_TYPE_REPOSITORY = "repository"
CMP_TYPE_ZIP_FILES = "zip file"
CMP_TYPE_GZIP_FILES = "gzip file"
CMP_TYPE_KABI = "kabi"
CMP_TYPE_DRIVE_KABI = "drive kabi"
CMP_TYPE_KCONFIG = "kconfig"
CMP_TYPE_KCONFIG_DRIVE = "drive kconfig"
CMP_TYPE_RPM_LEVEL = 'rpm package name'
CMP_TYPE_RPM_ABI = "rpm abi"
CMP_TYPE_RPM_CONFIG = "rpm config"
CMP_TYPE_RPM_PROVIDES = "rpm provides"
CMP_TYPE_RPM_REQUIRES = "rpm requires"
CMP_TYPE_RPM_RUNNING = "rpm run help"
CMP_TYPE_RPM_CMDS = "rpm cmds"
CMP_TYPE_RPM_SERVICES = "rpm services"
CMP_TYPE_RPM_FILES = "rpm files"
CMP_TYPE_RPM_KERNEL_CONFIG = "kernel config"
CMP_TYPE_RPM_KERNEL_ABI = "kernel abi"
CMP_TYPE_ISO_RPM_FILES = "iso rpm"
CMP_TYPE_REPOSITORY_RPMS = "iso rpm"
CMP_TYPE_RPMS_TEST = "rpm test"
CMP_TYPE_PERFORMANCE = "performance"
CMP_TYPE_SERVICE = "rpm service"
CMP_TYPE_SERVICE_DETAIL = 'service detail'
CMP_TYPE_CI_CONFIG = 'ciconfig'
CMP_TYPE_CI_FILE_CONFIG = 'ci file config'
CMP_TYPE_AT = 'AT'
CMP_TYPE_CMD = 'rpm cmd'
CMP_TYPE_RPM_HEADER = 'rpm header'
CMP_TYPE_RPM_LIB = 'rpm lib'
CMP_TYPE_DIFFERENCES = 'differences'
CMP_TYPE_REQUIRES = "requires"

# COMPOSITE_CMPS which without detail report
COMPOSITE_CMPS = {CMP_TYPE_RPM, CMP_TYPE_REPOSITORY}
RESULT_SAME = {"1", "1.1", "2", "same", "100%"}
RESULT_DIFF = {"3", "changed", "diff"}
RESULT_LESS = {"4", "less"}
RESULT_MORE = {"5", "more"}

SIMILARITY_TYPES = {
    CMP_TYPE_RPM_ABI,
    CMP_TYPE_KABI,
    CMP_TYPE_DRIVE_KABI,
    CMP_TYPE_KCONFIG,
    CMP_TYPE_KCONFIG_DRIVE,
    CMP_TYPE_RPM_CONFIG,
    CMP_TYPE_SERVICE_DETAIL,
}

PKG_SIMILARITY_SON_TYPES = {
    CMP_TYPE_RPM_PROVIDES,
    CMP_TYPE_RPM_REQUIRES,
    CMP_TYPE_RPM_FILES
}

CMP_SAME_RESULT = [CMP_RESULT_SAME, CMP_RESULT_CHANGE]

# EXCEL COMMON PARAMETERS
REQUIRED_ROW = [9, 10, 12, 15, 16, 17, 18]
FONT_SIZE = 18
FIFTEEN_ROW = 15
FOURTEEN_ROW = 14
THIRTEEN_ROW = 13
TWELVE_ROW = 12
ELEVEN_ROW = 11
TEN_ROW = 10
SIX_ROW = 6
FIVE_ROW = 5
THREE_ROW = 3
TWO_ROW = 2
SEVEN_COLUMN = 7
SIX_COLUMN = 6
FIVE_COLUMN = 5
FOUR_COLUMN = 4
TWO_COLUMN = 2
SIX_TITLE = ["基于", "的版本"]
ELEVEN_TITLE = ["OSV内核KABI接口白名单与", "内核KABI接口白名单一致性比例"]
TWELVE_TITLE = ["OSV软件包ABI接口与", "软件包ABI一致性比例"]
THIRTEEN_TITLE = ["OSV软件包Service文件与", "软件包Service文件一致性比例"]
FOURTEEN_TITLE = ["OSV软件包配置文件与", "软件包配置文件一致性比例"]
FIFTEEN_TITLE = ["OSV的内核配置与", "一致性比例"]

# Some file category filtering re pattern
FILTER_PATTERN = {
    "config": "^/etc/.*\\.conf$",
    "header": ".*\\.h$",
    "service": "^/usr/lib/systemd/system/.*\\.service$",
    "jabi": ".*\\.jar$",
    "abi": ".*\\.so$",
    "cmd_1": "^/usr/bin/.*",
    "cmd_2": "^/usr/sbin/.*",
    "cmd_3": "^/usr/local/bin/.*",
    "cmd_4": "^/usr/local/sbin/.*",
    "cmd_5": "^/bin/.*",
    "build": "^/usr/lib/.build-id/.*",
    "ima": "^/etc/ima/.*"
}
NO_FILES = "(没有包含文件)"

# The similarity item displayed in the JSON report
TOOLS_RESULT_ITEMS = ['core_pkg', 'level2 pkg', 'kabi', 'level2 rpm abi', 'service detail',
                      'rpm config', 'kconfig']
PLATFORM_RESULT_ITEMS = ['rpm test', 'AT', 'performance', 'ciconfig']

# DETAIL PATH
DETAIL_PATH = "details_analyse"

# The Column names of the Details in the RPM REPORT
ALL_DETAILS_NAME = ['effect drivers', 'details path']

# The Character in File name have changed.
OLD_CHAR = ('oe1',)
NEW_CHAR = {'oe1': ['ky10']}

# All Kernel Binary Package Name
KERNEL = 'kernel'
OTHER_KERNEL_NAMES = ['kernel-core', 'kernel-default']

# ABI DETAILS COUNT RESULT
COUNT_ABI_DETAILS = {
    'remove_abi': 0,
    'change_abi': 0,
    'add_abi': 0
}
# Dist name
DIST_FLAG = ['el8', 'el7', 'oe1', 'an8', 'ctl2', 'ky10', 'ky3', 'eulerosv2r9', 'eulerosv2r10', 'eulerosv2r11']

RPMFILE_CMP_TYPES = [CMP_TYPE_SERVICE, CMP_TYPE_RPM_CONFIG, CMP_TYPE_RPM_HEADER, CMP_TYPE_RPM_FILES,
                     CMP_TYPE_RPM_LIB, CMP_TYPE_CMD]
KERNEL_ANALYSE = [CMP_TYPE_DRIVE_KABI, CMP_TYPE_KCONFIG_DRIVE, CMP_TYPE_KABI, CMP_TYPE_KCONFIG]
COUNT_RESULTS = [CMP_RESULT_MORE, CMP_RESULT_LESS, CMP_RESULT_SAME, CMP_RESULT_DIFF]
CMP_TYPE = "compare type"
CMP_RESULT = "compare result"
CTG_LEVEL = "category level"
