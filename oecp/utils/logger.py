# -*- encoding=utf-8 -*-
"""
# **********************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# [oecp] is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# **********************************************************************************
"""
import os
import logging.config


def init_logger():
    """
    初始化logger
    :return:
    """
    conf_path = os.path.realpath(os.path.join(os.path.dirname(__file__), "../conf/logger.conf"))
    log_path = '/var/log/oecp'
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    defaults = {}
    defaults['args'] = (os.path.join(log_path, 'oecp.log'), 'a+', 50 * 1024 * 1024, 5)
    logging.config.fileConfig(conf_path, defaults=defaults)
