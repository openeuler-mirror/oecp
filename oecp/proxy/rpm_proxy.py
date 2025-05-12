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

from oecp.result.constants import STAND_DISTS, NO_CHECK_PKG

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
        return name, m.group(1)

    @classmethod
    def rpm_standard_dist(cls, rpm):
        """
        返回rpm包dist标识
        :param rpm: 寻找标准包名解析, eg: "gcc-10.3.1-17.oe2203.aarch64.rpm"
        :return: distribution 标识
        """
        m = re.match(r"^.+-.+-(.+)", rpm)

        if m:
            d = re.search(r"oe\w+", m.group(1))
            return d.group() if d else ''
        return ''

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
                m = re.match(r"-(.+)\.(.+)\.rpm", rpm.replace(name + '-' + version, "", 1))
                if not m:
                    # eg: RAID-3858_3758-EulerOS2.10-hiraid-1.0.0.18-aarch64.rpm
                    m = re.match(r"-(.+)\.rpm", rpm.replace(name + '-' + version, "", 1))
                    return name, version, '', '', m.group(1)
                r_d, arch = m.group(1), m.group(2)
                for d_flag in STAND_DISTS.values():
                    if not d_flag or d_flag not in r_d:
                        continue
                    else:
                        sp_release = r_d.split(d_flag)[0].rstrip('.')
                        release = re.sub(r'.module[_+]+', '.module', sp_release)
                        d = d_flag + r_d.split(d_flag)[1]
                        # eg: caja-core-extensions-1.22.0-1.ky3.kb58.x86_64.rpm
                        kb_num = re.search(r"kb\d+", d)
                        if kb_num:
                            release = release + '.' + kb_num.group()
                            d = d.split(kb_num.group())[0].rstrip('.')
                        return name, version, release, d, arch
                m = re.match(r"([\d._]+)\.([a-zA-Z]\w+)", r_d)
                if m:
                    return name, version, m.group(1), m.group(2), arch
                else:
                    # 名称-版本号-发布号.体系.rpm
                    # eg: grpc-1.31.0-6.x86_64.rpm
                    return name, version, r_d, '', arch
            elif dist == "category":
                # 名称-版本号-发布号.发行商-类型
                # eg: texlive-base-20180414-28.oe1.oecp
                m = re.match(r"^(.+)-(.+)-(.+)\.(.+)\.(.+)", rpm)
                return m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)

            return (None,) * 5
        except AttributeError as attr_error:
            logger.exception("Package %s attribute matching error, %s" % rpm, attr_error)
        except Exception as general_error:
            logger.exception(f"prase {rpm} rpm name error: {general_error}")

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
        # 对特定包不做检查
        if cls.rpm_name(rpm) in NO_CHECK_PKG:
            return False

        return not ("-javadoc-" in rpm or "-doc-" in rpm or "-docs-" in rpm
                    or "-debuginfo-" in rpm or "-debugsource-" in rpm
                    or ".oecp.rpm" in rpm or "-help-" in rpm
                    )

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
