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
# Create: 2022-3-05
# Description: test rpm name prase
# **********************************************************************************
"""
import logging
from unittest import TestCase

from oecp.proxy.rpm_proxy import RPMProxy
from oecp.utils.logger import init_logger


class TestRPMProxy(TestCase):
    @classmethod
    def setUpClass(cls):
        init_logger()
        cls.logger = logging.getLogger("test")

    def test_rpm_name_proxy(self):
        rpm_proxy = RPMProxy()
        self.assertEqual(rpm_proxy.rpm_name("partclone-0.3.12-4.oe2203.rpm"), "partclone")
        self.assertEqual(rpm_proxy.rpm_name("netsniff-ng-0.6.8-1.oe2203.rpm"), "netsniff-ng")
        self.assertEqual(rpm_proxy.rpm_name("openapi-spec-validator-help-0.3.1-1.oe2203.noarch.rpm"),
                         "openapi-spec-validator-help")


