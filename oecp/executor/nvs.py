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
import json
import os
from oecp.main.mapping import SQLiteMapping
from oecp.executor.base import CompareExecutor, CPM_CATEGORY_DIFF
from oecp.result.compare_result import CMP_TYPE_RPM, CompareResultComposite, CompareResultComponent, CMP_RESULT_SAME, \
    CMP_RESULT_DIFF, CMP_TYPE_DRIVE_KABI
from oecp.proxy.rpm_proxy import RPMProxy
from oecp.result.constants import CMP_TYPE_REQUIRES, CMP_TYPE_PROVIDES

logger = logging.getLogger('oecp')


class NVSCompareExecutor(CompareExecutor):

    def __init__(self, base_dump, other_dump, config=None):
        super(NVSCompareExecutor, self).__init__(base_dump, other_dump, config)
        self.base_dump = base_dump.run()
        self.other_dump = other_dump.run()
        self.mapping = {}
        self._data = 'data'
        self.config = config if config else {}
        self.instantiation_mapping()

    @staticmethod
    def _kabi_get_driver(kabi):
        drivers = []
        kind_kabi_file = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                      "conf/kabi_whitelist/aarch64_kind_drive_kabi")
        with open(kind_kabi_file, 'r') as fd:
            dict_kind_driver = json.load(fd)
        for driver, kabi_lists in dict_kind_driver.items():
            if kabi in kabi_lists:
                drivers.append(driver)
        return ','.join(drivers)

    def instantiation_mapping(self):
        for side in self.config.get('sqlite_path', {}).keys():
            for base_sqlite in self.config.get('sqlite_path').get(side, []):
                self.mapping.setdefault(side, [])
                if isinstance(base_sqlite, dict):
                    for sqlite in base_sqlite.values():
                        self.mapping.get(side).append(SQLiteMapping(sqlite))
                elif not isinstance(base_sqlite, str):
                    repo_path = os.path.join(base_sqlite.name, 'repodata')
                    for repo_file in os.listdir(repo_path):
                        if '-primary.sqlite.' in repo_file:
                            sqlite = os.path.join(repo_path, repo_file)
                            self.mapping.get(side).append(SQLiteMapping(sqlite))

    def to_pretty_dump(self, dump):
        """
        以provides为例， 去除rpm和provide的release转化为{'rpm': [provide1, provide2]}在进行比较
        @param dump: 原始dump
        @return: 比较所需的dump
        """
        pretty_dump = {}
        rpm_name = RPMProxy.rpm_name(dump['rpm'])
        for component in dump[self._data]:
            # requires 比较忽视release版本号，加上依赖类型（强依赖或弱依赖）
            if dump['kind'] == 'requires':
                requires_name = ' '.join([component['name'], component['symbol'], component['version'].split('-')[0]])
                new_component_dict = dict(name=requires_name, dependence=component['dependence'])
                pretty_dump.setdefault(rpm_name, []).append(new_component_dict)
            else:
                new_component_str = ' '.join([component['name'], component['symbol'], component['version']])
                pretty_dump.setdefault(rpm_name, []).append(new_component_str)
        return rpm_name, pretty_dump

    def get_all_requires_rpm(self, dump, all_mapping):
        all_requires_rpm = []
        for mapping in all_mapping:
            for component in dump[self._data]:
                requires_name, symbol, version = component['name'].strip(), component['symbol'].strip(), component[
                    'version'].strip()
                packages = mapping.get_provides_rpm(requires_name, symbol, version)
                requires_info = ' '.join([component['name'], component['symbol'], component['version'].split('-')[0]])
                require_result = dict(name=requires_info, packages=','.join(packages) if packages else '',
                                      dependence=component['dependence'])
                all_requires_rpm.append(require_result)

        return all_requires_rpm

    def cmp_component_set(self, base_dump, other_dump, base_components, other_components):
        """
        providers或者requires组件比较
        @param base_components: 集合组件base
        @param other_components: 集合组件other
        @param single_result: 初始结果为same，集合组件遍历若有一项差异设为diff
        @return:
        """
        single_result = CMP_RESULT_SAME
        count_result = {'same': 0, 'more': 0, 'less': 0, 'diff': 0}
        rpm_version_release_dist = self.extract_version_flag(base_dump['rpm'], other_dump['rpm'])
        category = base_dump['category'] if base_dump['category'] == other_dump['category'] else CPM_CATEGORY_DIFF
        if base_dump['kind'] == 'kabi' or base_dump['kind'] == 'kconfig':
            component_results = self.format_dump_kv(base_components, other_components, base_dump['kind'])
        elif base_dump['kind'] == CMP_TYPE_REQUIRES:
            component_results = self.format_rmp_name(base_components, other_components)
        else:
            component_results = self.format_dump_provides(base_components, other_components, rpm_version_release_dist)

        result = CompareResultComposite(CMP_TYPE_RPM, single_result, base_dump['rpm'], other_dump['rpm'], category)
        for component_result in component_results:
            for sub_component_result in component_result:
                self.count_cmp_result(count_result, sub_component_result[-1])
                if self.config.get('compare_type') == CMP_TYPE_DRIVE_KABI and sub_component_result[
                    -1] != CMP_RESULT_SAME:
                    eff_drives = self._kabi_get_driver(sub_component_result[0].split()[0])
                    data = CompareResultComponent(self.config.get('compare_type'), sub_component_result[-1],
                                                  sub_component_result[0], sub_component_result[1], eff_drives)
                else:
                    data = CompareResultComponent(self.config.get('compare_type'), sub_component_result[-1],
                                                  sub_component_result[0], sub_component_result[1])
                if sub_component_result[-1] != CMP_RESULT_SAME and single_result == CMP_RESULT_SAME:
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
                base_dump, other_dump = single_pair[0], single_pair[1]
                if self.mapping:
                    base_components = self.get_all_requires_rpm(base_dump, self.mapping.get('side_a'))
                    other_components = self.get_all_requires_rpm(other_dump, self.mapping.get('side_b'))
                elif base_dump['kind'] == CMP_TYPE_PROVIDES:
                    base_components = base_dump[self._data]
                    other_components = other_dump[self._data]
                else:
                    base_rpm_version, base_pretty_dump = self.to_pretty_dump(base_dump)
                    other_rpm_version, other_pretty_dump = self.to_pretty_dump(other_dump)
                    if base_dump['kind'] == CMP_TYPE_REQUIRES:
                        base_components = base_pretty_dump.get(base_rpm_version)
                        other_components = other_pretty_dump.get(other_rpm_version)
                    else:
                        base_components = set(base_pretty_dump.get(base_rpm_version))
                        other_components = set(other_pretty_dump.get(other_rpm_version))
                result = self.cmp_component_set(base_dump, other_dump, base_components, other_components)
                compare_list.append(result)
        return compare_list

    def run(self):
        result = self.compare()
        if not result:
            logger.warning('compare result empty, %s, %s', self.base_dump, self.other_dump)
        return result
