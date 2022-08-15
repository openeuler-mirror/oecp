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
# **********************************************************************************
"""

import logging
from oecp.executor.base import CompareExecutor

logger = logging.getLogger('oecp')


class FindSensitiveInfoExecutor(CompareExecutor):

    def __init__(self, dump_a, config=None):
        super(FindSensitiveInfoExecutor, self).__init__(dump_a, None, config)
        assert hasattr(dump_a, 'run'), 'dump should be a object with "run" method'
        self.dump_a = dump_a.run()
        self._data = 'data'
        self.config = config if config else {}

    def run(self):
        result = self.dump_a
        if not result:
            logger.warning(f"Can not find sensitive info in {self.dump_a}")
        return result
