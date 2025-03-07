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
import os.path

from pathlib import Path
from oecp.executor.base import CompareExecutor
from oecp.main.extract_kapi import EXTRACTKAPI
from oecp.proxy.rpm_proxy import RPMProxy
from oecp.result.compare_result import CompareResultComposite, CompareResultComponent
from oecp.result.constants import CMP_RESULT_SAME, CMP_TYPE_RPM, CMP_RESULT_DIFF, CMP_SERVICE_SAME

logger = logging.getLogger('oecp')


class KAPICompareExecutor(CompareExecutor):
    def __init__(self, base_dump, other_dump, config=None):
        super(KAPICompareExecutor, self).__init__(base_dump, other_dump, config)
        self.base_dump = base_dump.run()
        self.other_dump = other_dump.run()
        self.config = config if config else {}

    def get_src_kpath(self, dump):
        rpm_name = dump.get("rpm")
        _, k_v, k_r, _, _ = RPMProxy.rpm_n_v_r_d_a(rpm_name)
        kpath = self.config.get("src_kernel")
        if not kpath:
            logger.error("Please input the storage path of the kernel source rpms with -s (--src_kernel).")
            return None
        path = Path(kpath)
        src_kernel_rpms = [str(file) for file in path.rglob('*.src.rpm') if file.is_file()]
        for srpm in src_kernel_rpms:
            rpm_version = "-".join([k_v, k_r])
            srpm_name = os.path.basename(srpm)
            if rpm_version in srpm_name:
                source_path = RPMProxy.uncompress_source_rpm(srpm)

                return source_path

        logger.error("Not get %s srpm path, please check the version is same with kernel rpm or not." % rpm_name)

        return None

    def compare_result(self, base_dump, other_dump, single_result=CMP_RESULT_SAME):
        count_result = {'same': 0, 'more': 0, 'less': 0, 'diff': 0}
        base_kabi = [kabi.get("name") for kabi in base_dump.get("data")]
        other_kabi = [kabi.get("name") for kabi in other_dump.get("data")]
        category = base_dump['category']
        base_srpm_obj = self.get_src_kpath(base_dump)
        other_srpm_obj = self.get_src_kpath(other_dump)
        result = CompareResultComposite(CMP_TYPE_RPM, single_result, base_dump['rpm'], other_dump['rpm'], category)
        if not base_srpm_obj or not other_srpm_obj:
            logger.error(f"not get source code path {base_srpm_obj}, {other_srpm_obj}")
            return result
        extract_kapi = EXTRACTKAPI()
        base_kapi = extract_kapi.order_get_prototype(base_kabi, base_srpm_obj)
        other_kapi = extract_kapi.order_get_prototype(other_kabi, other_srpm_obj)
        component_results = self.format_func_prototype(base_kapi, other_kapi)
        for component_result in component_results:
            for sub_component_result in component_result:
                self.count_cmp_result(count_result, sub_component_result[-1])
                data = CompareResultComponent(self.config.get('compare_type'), sub_component_result[2],
                                        sub_component_result[0], sub_component_result[1], sub_component_result[-1])
                if sub_component_result[-1] not in CMP_SERVICE_SAME:
                    single_result = CMP_RESULT_DIFF
                    result.set_cmp_result(single_result)
                result.add_component(data)
        result.add_count_info(count_result)

        return result

    def compare(self):
        compare_list = []
        similar_dumpers = self.get_similar_rpm_pairs(self.base_dump, self.other_dump)
        for single_pair in similar_dumpers:
            if single_pair:
                result = self.compare_result(single_pair[0], single_pair[1])

            compare_list.append(result)

        return compare_list

    def run(self):
        result = self.compare()
        if not result:
            logger.warning('compare result empty, %s, %s', self.base_dump, self.other_dump)
        return result
