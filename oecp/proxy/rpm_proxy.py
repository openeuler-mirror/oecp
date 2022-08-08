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
# Create: 2021-09-03
# Description: rpm proxy
# **********************************************************************************
"""
import re
import subprocess
import logging

from oecp.result.constants import DIST_FLAG

logger = logging.getLogger('oecp')


class RPMProxy(object):
    """
    rpm包代理，实现常见的rpm操作
    """

    @classmethod
    def rpm_name(cls, rpm):
        """
        返回rpm包名称
        :param rpm:
        :return:
        """
        m = re.match(r"^(.+)-.+-.+", rpm)

        if m:
            return m.group(1)
        else:
            return rpm

    @classmethod
    def rpm_name_version(cls, rpm):
        name = cls.rpm_name(rpm)
        m = re.match(r"-(.+)-.+", rpm.replace(name, "", 1))
        if m:
            return name, m.group(1)
        else:
            logger.error("Failed to resolve the rpm version.")

    @classmethod
    def rpm_n_v_r_d_a(cls, rpm, dist="openEuler"):
        """
        解析rpm包的名称、版本号、发布号、发行商、体系
        :param rpm:
        :param dist:
        :return:
        """
        try:
            if dist == "openEuler":
                # 名称-版本号-发布号.发行商.体系.rpm
                # eg: grpc-1.31.0-6.oe1.x86_64.rpm
                name, version = cls.rpm_name_version(rpm)
                m = re.match(r"-(.+)\.rpm", rpm.replace(name + '-' + version, "", 1))
                r_d_a = m.group(1)
                arch = r_d_a.split('.')[-1]
                r_d = r_d_a.rstrip(arch).rstrip('.')
                prase = False
                release, dist = '', ''
                for d_flag in DIST_FLAG:
                    if d_flag not in r_d:
                        continue
                    else:
                        prase = True
                        first_r = r_d.split(d_flag)[0]
                        first_d = r_d.split(d_flag)[-1]
                        release = re.sub(r'.module[_+]+', '', first_r).strip('.')
                        dist = d_flag + first_d
                if not prase:
                    m = re.match(r"([\d._]+)\.(.+)", r_d)
                    if m:
                        return name, version, m.group(1), m.group(2), arch
                    else:
                        release = r_d
                return name, version, release, dist, arch
            elif dist == "category":
                # 名称-版本号-发布号.发行商-类型
                # eg: texlive-base-20180414-28.oe1.oecp
                m = re.match(r"^(.+)-(.+)-(.+)\.(.+)\.(.+)", rpm)
                return m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)

            return (None,) * 5
        except AttributeError as attr_error:
            logger.exception("Package attribute matching error, %s" % attr_error)
        except Exception as general_error:
            logger.exception(general_error)

    @classmethod
    def is_rpm_file(cls, rpm):
        return rpm.endswith(".rpm")

    @classmethod
    def is_rpm_focus_on(cls, rpm):
        """
        关注的rpm包
        :param rpm:
        :return:
        """
        return not ("-javadoc-" in rpm or "-doc-" in rpm or "-docs-" in rpm
                    or "-debuginfo-" in rpm or "-debugsource-" in rpm
                    or ".oecp.rpm" in rpm
                    or "-help-" in rpm)

    @classmethod
    def is_debuginfo_rpm(cls, rpm):
        """
        debuginfo包
        :param rpm:
        :return:
        """
        return "-debuginfo-" in rpm

    @classmethod
    def correspond_debuginfo_name(cls, rpm):
        """
        将rpm包名称增加 "-debuginfo-"
        :param rpm:
        :return:
        """
        name = cls.rpm_name(rpm)
        return rpm.replace(name, f"{name}-debuginfo")

    @classmethod
    def query_dump(cls, rpm):
        pass

    @classmethod
    def extract(cls, rpm):
        pass

    @classmethod
    def query_provides(cls, rpm):
        pass

    @classmethod
    def query_requires(cls, rpm):
        pass

    @classmethod
    def perform_cpio(cls, package):
        """
        解压rpm包
        @param package: rpm包路径
        @return: None
        """
        stdin = subprocess.Popen(['rpm2cpio', package], stdout=subprocess.PIPE)
        p = subprocess.Popen(['cpio', '-d', '-i'],
                             stdin=stdin.stdout,
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.STDOUT)
        p.communicate()
