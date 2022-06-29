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

import logging
import json
import os
from oecp.main.mapping import SQLiteMapping
from oecp.executor.base import CompareExecutor, CPM_CATEGORY_DIFF
from oecp.result.compare_result import CMP_TYPE_RPM, CompareResultComposite, CompareResultComponent, CMP_RESULT_SAME, \
    CMP_RESULT_DIFF, CMP_TYPE_DRIVE_KABI
from oecp.proxy.rpm_proxy import RPMProxy
from oecp.result.constants import CMP_RESULT_CHANGE, CMP_TYPE_REQUIRES

logger = logging.getLogger('oecp')


class NVSCompareExecutor(CompareExecutor):

    def __init__(self, dump_a, dump_b, config=None):
        super(NVSCompareExecutor, self).__init__(dump_a, dump_b, config)
        assert hasattr(dump_a, 'run'), 'dump should be a object with "run" method'
        assert hasattr(dump_b, 'run'), 'dump should be a object with "run" method'
        self.dump_a = dump_a.run()
        self.dump_b = dump_b.run()
        self.mapping = {}
        self._data = 'data'
        self.config = config if config else {}
        self.instantiation_mapping()

    @staticmethod
    def _count_result(count_result, cmp_result):
        if cmp_result == 'more':
            count_result["more_count"] += 1
        elif cmp_result == 'less':
            count_result["less_count"] += 1
        elif cmp_result == 'diff':
            count_result["diff_count"] += 1

    def instantiation_mapping(self):
        for side in self.config.get('sqlite_path', {}).keys():
            for sqlite_a in self.config['sqlite_path'].get(side, []):
                if not isinstance(sqlite_a, str):
                    repo_path = os.path.join(sqlite_a.name, 'repodata')
                    for file in os.listdir(repo_path):
                        if '-primary.sqlite.' in file:
                            sqlite_a = os.path.join(repo_path, file)
                self.mapping.setdefault(side, [])
                self.mapping[side].append(SQLiteMapping(sqlite_a))

    def _to_pretty_dump(self, dump):
        """
        以provides为例， 去除rpm和provide的release转化为{'rpm': [provide1, provide2]}在进行比较
        @param dump: 原始dump
        @return: 比较所需的dump
        """
        pretty_dump = {}
        rpm_n = RPMProxy.rpm_n_v_r_d_a(dump['rpm'])[0]
        for component in dump[self._data]:

            # provides 和 requires 比较忽视release版本号
            if dump['kind'] in ('provides', 'requires'):
                new_component = ' '.join([component['name'], component['symbol'], component['version'].split('-')[0]])
            else:
                new_component = ' '.join([component['name'], component['symbol'], component['version']])
            pretty_dump.setdefault(rpm_n, []).append(new_component)
        return rpm_n, pretty_dump

    def _kabi_get_driver(self, kabi):
        drivers = []
        kind_kabi_file = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                      "conf/kabi_whitelist/aarch64_kind_drive_kabi")
        with open(kind_kabi_file, 'r') as fd:
            dict_kind_driver = json.load(fd)
        for driver in dict_kind_driver.keys():
            if kabi in dict_kind_driver[driver]:
                drivers.append(driver)
        return ','.join(drivers)

    def _get_all_requires_rpm(self, dump, all_mapping):
        all_requires_rpm = []
        for mapping in all_mapping:
            for component in dump[self._data]:
                if component['name'].startswith('rpmlib'):
                    continue
                name, symbol, version = component['name'].strip(), component['symbol'].strip(), component[
                    'version'].strip()
                packages = mapping.get_provides_rpm(name, symbol, version)
                all_requires_rpm.extend(packages)

        return set(all_requires_rpm)

    def _cmp_component_set(self, dump_a, dump_b, components_a, components_b, single_result=CMP_RESULT_SAME):
        """
        providers或者requires组件比较
        @param components_a: 集合组件a
        @param components_b: 集合组件b
        @param single_result: 初始结果为same，集合组件遍历若有一项差异设为diff
        @return:
        """
        count_result = {'more_count': 0, 'less_count': 0, 'diff_count': 0}
        assert isinstance(components_a, set), '%s should be a set type' % components_a
        assert isinstance(components_b, set), '%s should be a set type' % components_b
        category = dump_a['category'] if dump_a['category'] == dump_b[
            'category'] else CPM_CATEGORY_DIFF
        if dump_a['kind'] == 'kabi' or dump_a['kind'] == 'kconfig':
            component_results = self.format_dump_kv(components_a, components_b, dump_a['kind'])
        elif dump_a['kind'] == CMP_TYPE_REQUIRES:
            component_results = self.format_rmp_name(components_a, components_b)
        else:
            component_results = self.format_dump(components_a, components_b)

        result = CompareResultComposite(CMP_TYPE_RPM, single_result, dump_a['rpm'], dump_b['rpm'], category)
        for component_result in component_results:
            for sub_component_result in component_result:
                self._count_result(count_result, sub_component_result[-1])
                if self.config.get('compare_type') == CMP_TYPE_DRIVE_KABI and sub_component_result[
                    -1] != CMP_RESULT_SAME:
                    eff_drives = self._kabi_get_driver(sub_component_result[0].split()[0])
                    data = CompareResultComponent(self.config.get('compare_type'), sub_component_result[-1],
                                                  sub_component_result[0], sub_component_result[1], eff_drives)
                else:
                    data = CompareResultComponent(self.config.get('compare_type'), sub_component_result[-1],
                                                  sub_component_result[0], sub_component_result[1])
                if sub_component_result[-1] not in [CMP_RESULT_SAME,
                                                    CMP_RESULT_CHANGE] and single_result == CMP_RESULT_SAME:
                    single_result = CMP_RESULT_DIFF
                    result.set_cmp_result(single_result)
                result.add_component(data)
        result.add_count_info(count_result)

        return result

    def compare(self):
        compare_list = []
        for dump_a in self.dump_a:
            for dump_b in self.dump_b:
                # 取rpm name 相同进行比较
                if RPMProxy.rpm_name(dump_a['rpm']) == RPMProxy.rpm_name(dump_b['rpm']) or dump_a['kind'] == 'kabi' \
                     or dump_a['kind'] == 'kconfig':
                    if self.mapping:
                        components_a = self._get_all_requires_rpm(dump_a, self.mapping['side_a'])
                        components_b = self._get_all_requires_rpm(dump_b, self.mapping['side_b'])
                    else:
                        rpm_v_a, pretty_dump_a = self._to_pretty_dump(dump_a)
                        rpm_v_b, pretty_dump_b = self._to_pretty_dump(dump_b)
                        components_a, components_b = set(pretty_dump_a[rpm_v_a]), set(pretty_dump_b[rpm_v_b])
                    result = self._cmp_component_set(dump_a, dump_b, components_a, components_b)
                    compare_list.append(result)
        return compare_list

    def run(self):
        result = self.compare()
        if not result:
            logger.warning('compare result empty, %s, %s' % (self.dump_a, self.dump_b))
        return result
