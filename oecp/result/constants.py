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
# Description: compare result
# **********************************************************************************
"""
# COMPARE_RESULT
CMP_RESULT_MORE = "more"
CMP_RESULT_LESS = "less"
CMP_RESULT_DIFF = "diff"
CMP_RESULT_SAME = "same"
CMP_RESULT_CHANGE = "changed"
CMP_RESULT_LINK_CHANGE = "link changed"
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
CMP_TYPE_NAME = "name"
CMP_TYPE_RPM_KERNEL = "kernel"
CMP_TYPE_DIRECTORY = "repository directory"
CMP_TYPE_ISO = "iso"
CMP_TYPE_DIST_REPOSITORY = "dist repository"
CMP_TYPE_REPOSITORY = "repository"
CMP_TYPE_ZIP_FILES = "zip file"
CMP_TYPE_GZIP_FILES = "gzip file"
CMP_TYPE_KABI = "kabi"
CMP_TYPE_SYMBOL = "symbol"
CMP_TYPE_DRIVE_KABI = "drive kabi"
CMP_TYPE_KCONFIG = "kconfig"
CMP_TYPE_KCONFIG_DRIVE = "drive kconfig"
CMP_TYPE_RPM_LEVEL = 'rpm package name'
CMP_TYPE_RPM_ABI = "rpm abi"
CMP_TYPE_RPM_JABI = "rpm jabi"
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
CMP_TYPE_RPM_SERVICE = "rpm service"
CMP_TYPE_SERVICE_DETAIL = 'service detail'
CMP_TYPE_CI_CONFIG = 'ciconfig'
CMP_TYPE_CI_FILE_CONFIG = 'ci file config'
CMP_TYPE_AT = 'AT'
CMP_TYPE_CMD = 'rpm cmd'
CMP_TYPE_RPM_HEADER = 'rpm header'
CMP_TYPE_RPM_LIB = 'rpm lib'
CMP_TYPE_RPM_SYMBOL = 'rpm symbol'
CMP_TYPE_DIFFERENCES = 'differences'
CMP_TYPE_PROVIDES = "provides"
CMP_TYPE_ABI = "abi"
CMP_TYPE_CONFIG = "config"
CMP_TYPE_JABI = "jabi"
CMP_TYPE_SERVICE = "service"
CMP_TYPE_HEADER = 'header'
CMP_TYPE_KO = "ko"
CMP_TYPE_KO_INFO = "ko info"
CMP_TYPE_EXTRACT = "extract"

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
    CMP_TYPE_RPM_JABI,
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

# DETAILS COMPARE TYPES
DETAIL_CMP_TYPES = {
    CMP_TYPE_ABI,
    CMP_TYPE_CONFIG,
    CMP_TYPE_JABI,
    CMP_TYPE_SERVICE,
    CMP_TYPE_HEADER,
    CMP_TYPE_SYMBOL
}

CMP_SAME_RESULT = [CMP_RESULT_SAME, CMP_RESULT_CHANGE]
CMP_SERVICE_SAME = [CMP_RESULT_SAME, CMP_RESULT_MORE]

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
    "ko": ".*\\.ko(.xz)?$",
    "cmd": "^/usr/(local/)?(s)?bin/.*|^/bin/.*",
    "build": "^/usr/lib/.build-id/.*",
    "ima": "^/etc/ima/.*"
}

# The similarity item displayed in the JSON report
TOOLS_RESULT_ITEMS = ['core_pkg', 'level2 pkg', 'kabi', 'level2 rpm abi', 'service detail',
                      'rpm config', 'kconfig']
PLATFORM_RESULT_ITEMS = ['rpm test', 'AT', 'performance', 'ciconfig']

# The Column names of the Details in the RPM REPORT
ALL_DETAILS_NAME = ["effect drivers", "abi details"]

# ABI CHANGE TYPE
REMOVE_FUN = "Removed functions"
ADD_FUN = "Added functions"
CHANGE_FUN = "Changed functions"
CHANGE_VAR = "Changed variables"
ADD_VAR = "Added variables"
REMOVE_VAR = "Removed variables"
REMOVED_ABI = "Removed abi"
REMOVED_DEFINED = "Removed defined"

SYMBOL_TYPE = {
    REMOVE_FUN,
    CHANGE_FUN,
    CHANGE_VAR,
    REMOVE_VAR
}

# DATABASE BRANCH NAME
BRANCH_NAME = "branch_name"
DB_PASSWORD = "db_password"

# Get base and osv distribution.
BASE_SIDE = 'base'
OSV_SIDE = 'osv'

STAND_DISTS = {
    BASE_SIDE: "",
    OSV_SIDE: ""
}
OPENEULER = "openEuler"
UPSTREAM_DIST = {
    OPENEULER,
    "fedora"
}

# DETAIL REPROT DIRECTORY PATH
DETAIL_PATH = "details_analyse"

# BOTH OF OPENEULER ARCH
X86_64 = "x86_64"
AARCH64 = "aarch64"

# Special no check packages
NO_CHECK_PKG = [
    "kernel-source"
]

# Rename kernel src package
RENAME_KERNEL = [
  "kernel-kalt",
  "kernel-alt"
]

OBSOLETES = "Obsoletes"
PROVIDES = "Provides"

# RE PATTERNS
PAT_VER_CHANGED = [
    r"[-_.][a-z0-9]{64}\.",
    r"[a-z0-9]{38}\.",
    r"[-_.][a-z0-9]{32}(\.)?",
    r"[-_.][a-z0-9]{16}\.",
    r"[-.]\d(.\d){2}_[0-9a-z]{9}",
    r"python3-",
    r"py(thon)?[2,3]\.\w+",
    r"java-(\d+\.){0,2}\d+-openjdk-",
    r"([-_]?\d+)(\.\d+){0,3}"
]
PAT_DIR_VERSION = [
    r"[-/](\d+\.){0,3}\d+",
    r"java-(\d+\.){0,2}\d+-openjdk-",
    r"_(\d+\.){3}v\d{8}-\d{4}",
    r"py(thon)?[2,3]\.\d+"
]
PAT_SO = r"(-?\d*([-_.]\d+){0,3}(\.cpython-(.*)-linux-gnu)?\.(so|a)([-_.][\dA-Za-z]+){0,4})|-[a-z0-9]{16}.(so|rlib)"
PAT_JAR = r"[-_.]?(\d+[-.]){0,3}(v\d{8})?(-\d{4})?.?jar"

# COMPRESS FORMAT
CHANGE_FORMATS = [".md", ".xz"]

# BOTH ARCH OF DATABASES
ALL_ARCH = ["x86_64", "aarch64"]
