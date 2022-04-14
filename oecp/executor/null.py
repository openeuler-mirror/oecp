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
# **********************************************************************************
"""

from oecp.executor.base import CompareExecutor


class NullExecutor(CompareExecutor):

    def __init__(self, dump_a, dump_b, config=None):
        super(NullExecutor, self).__init__(dump_a, dump_b, config)
        if hasattr(dump_a, 'run') and hasattr(dump_b, 'run'):
            dump_a.run()
            dump_b.run()

    def run(self):
        return []
