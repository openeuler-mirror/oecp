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
# Create: 2021-09-06
# Description: compare result
# **********************************************************************************
"""
import os
import logging
import stat
import shutil
import operator
import uuid

from oecp.excel.create_web_show_result import WebShowResult
from oecp.excel.individual_statistics import IndividualStatistics
from oecp.excel.osv_data_summary import DataExcelFile
from oecp.result import export
from oecp.result.export import get_second_path
from oecp.result.json_result import json_result
from oecp.result.similar_result_calculate import calculate_similarity
from oecp.result.similarity import get_similarity
from oecp.result.test_result import performance_result_parser, test_result_parser, ciconfig_result_parser, \
    at_result_parser, assgin_rpm_summay
from oecp.result.constants import CMP_RESULT_DIFF, CMP_TYPE_DIFFERENCES, ALL_DETAILS_NAME, CMP_TYPE, COMPOSITE_CMPS, \
    CMP_TYPE_AT, CMP_TYPE_RPM, CMP_TYPE_CI_FILE_CONFIG, CMP_TYPE_CI_CONFIG, CMP_TYPE_PERFORMANCE, CMP_TYPE_RPMS_TEST, \
    CMP_TYPE_DRIVE_KABI, CMP_TYPE_SERVICE, CMP_TYPE_RPM_CONFIG, CMP_TYPE_RPM_ABI, CMP_TYPE_RPM_HEADER, \
    COUNT_ABI_DETAILS, CMP_TYPE_RPM_LEVEL, CMP_TYPE_RPM_REQUIRES, CMP_TYPE_SERVICE_DETAIL, DETAIL_PATH, CMP_RESULT_SAME

logger = logging.getLogger("oecp")


class CompareResultComponent(object):
    """
    比较结果对象
    """

    def __init__(self, cmp_type, cmp_result, cmp_side_a, cmp_side_b, detail=None, detail_file=None):
        """

        :param cmp_type: 比较名称，eg：kernel abi，kernel config
        :param cmp_result: 比较结果
        :param cmp_side_a: 比较对象
        :param cmp_side_b: 比较对象
        :param detail: 比较结果详细内容路径
        """
        self.cmp_type = cmp_type
        self.cmp_result = cmp_result
        self.cmp_side_a = cmp_side_a
        self.cmp_side_b = cmp_side_b
        self.detail = detail
        self.detail_file = detail_file
        self._binary_rpm_package = None
        self._source_package = None
        self._level = None

    def set_cmp_type(self, cmp_type):
        """

        :param cmp_type:
        :return:
        """
        self.cmp_type = cmp_type

    def set_binary_rpm_package(self, binary_rpm_package):
        self._binary_rpm_package = binary_rpm_package

    def set_cmp_result(self, cmp_result):
        """
        需要根据叶子节点结果判断父节点结果来设置父节点结果
        @param cmp_result:
        @return:
        """
        self.cmp_result = cmp_result

    def set_source_package(self, source_package):
        self._source_package = source_package

    def set_level(self, level):
        """
        :param level: rpm包的兼容性等级
        """
        self._level = level

    def __str__(self):
        return "{} {} {} {} {}".format(
            self.cmp_type, self.cmp_result, self.cmp_side_a, self.cmp_side_b, self.detail)


class CompareResultComposite(CompareResultComponent):
    """
    复合比较结果对象
    """

    def __init__(self, cmp_type, cmp_result, cmp_side_a, cmp_side_b, detail=None, count_result=None):
        """

        :param cmp_type:
        :param cmp_result:
        :param cmp_side_a:
        :param cmp_side_b:
        :@param detail:
        """
        super(CompareResultComposite, self).__init__(cmp_type, cmp_result, cmp_side_a, cmp_side_b)

        # 复合比较结果为rpm层时，需要加上category信息
        self.detail = detail
        self.diff_components = []  # 比较结果对象列表
        self.count_result = count_result

    def add_component(self, *diff_components):
        """

        :param diff_components:
        :return:
        """
        self.diff_components.extend(diff_components)

    def add_count_info(self, count_result):
        self.count_result = count_result

    def set_cmp_result(self, cmp_result=None):
        if cmp_result:
            super(CompareResultComposite, self).set_cmp_result(cmp_result)
            return
        for diff_component in self.diff_components:
            if diff_component.cmp_result == CMP_RESULT_DIFF:
                self.cmp_result = CMP_RESULT_DIFF
                break
        else:
            self.cmp_result = CMP_RESULT_SAME

    def __str__(self):
        """

        :return:
        """
        string = ["{} {} {} {} {}".format(
            self.cmp_type, self.cmp_result, self.cmp_side_a, self.cmp_side_b, self.detail)] + \
                 [str(component) for component in self.diff_components]
        return "\n".join(string)

    def export(self, *e_args):
        root_path, result_format, iso_path, platform_path = e_args
        base_side_a, base_side_b = format_base_side(self.cmp_side_a, self.cmp_side_b, iso_path)
        osv_title = 'report-' + get_title(base_side_a) + '-' + get_title(base_side_b)
        export_floder = os.path.join(root_path, osv_title)
        if os.path.exists(export_floder):
            shutil.rmtree(export_floder)

        # all result which need to export as csv
        rows = {}
        count_abi = {
            "all_packages_abi": [0, 0, 0],
            "l1_packages_abi": [0, 0, 0],
            "l2_packages_abi": [0, 0, 0]
        }
        all_report_path = os.path.join(root_path, osv_title)
        parse_result(self, base_side_a, base_side_b, rows, count_abi, all_report_path)
        if result_format == 'json':
            result = json_result(rows, base_side_a, base_side_b)
            export.export_json(root_path, 'osv', osv_title, result)
            details_path = os.path.join(root_path, osv_title, DETAIL_PATH)
            if os.path.exists(details_path):
                shutil.rmtree(details_path)
            logger.info(
                f"all results have compare done, please check: {os.path.join(os.path.realpath(root_path), osv_title)}")
            return osv_title

        performance_rows = performance_result_parser(base_side_a, base_side_b, platform_path)
        rpm_test_rows, rpm_test_details = test_result_parser(base_side_a, base_side_b, platform_path)
        ciconfig_rows, file_config_rows = ciconfig_result_parser(base_side_a, base_side_b, platform_path)
        at_rows = at_result_parser(base_side_b, platform_path)
        if ciconfig_rows:
            rows[CMP_TYPE_CI_CONFIG] = ciconfig_rows
        if file_config_rows:
            rows[CMP_TYPE_CI_FILE_CONFIG] = file_config_rows
        if performance_rows:
            rows[CMP_TYPE_PERFORMANCE] = performance_rows
        if rpm_test_rows and rpm_test_details:
            rows[CMP_TYPE_RPM] = rows[CMP_TYPE_RPM] + rpm_test_rows
            # there is a pkg named: rpm
            # the test result  will cover rows[CMP_TYPE_RPM], so can not use rows.update
            # rows.update(rpm_test_details)
            rows[CMP_TYPE_RPMS_TEST] = rpm_test_details
            test_summary = assgin_rpm_summay(rpm_test_details, base_side_a, base_side_b)
            rows["rpm-test"] = test_summary
        if at_rows:
            rows[CMP_TYPE_AT] = at_rows

        similarity = get_similarity(rows, base_side_a, base_side_b)
        # Write data to excel
        excel_file = DataExcelFile()
        args = (similarity, base_side_a, base_side_b, root_path, osv_title, iso_path[1])
        excel_file.write_summary_file(*args)
        web_show_result = WebShowResult(excel_file.tools_result, excel_file.conclusion)
        web_show_result.write_json_result(*args)
        rows["similarity"] = [similarity]
        differences = get_differences_info(rows)
        if differences:
            rows[CMP_TYPE_DIFFERENCES] = differences

        for node, value in rows.items():
            if node == CMP_TYPE_RPMS_TEST:
                for sub_node, sub_value in value.items():
                    export_single_report(sub_node, sub_value, root_path, osv_title)
                continue
            # eg: node is rpm

            if isinstance(value, list):
                report_name = 'all-' + node.replace(' ', '-') + '-report'
                report_path = export.create_directory(root_path, report_name, osv_title)
                headers = value[0].keys()
                if node == CMP_TYPE_RPM:
                    # add explanation for rpm package name result
                    explan = "rpm package name explain:\n\
                    1   -- same name + version + release num + distributor\n\
                    1.1 -- same name + version + release num\n\
                    2   -- same name + version\n\
                    3   -- same name\n\
                    4   -- less\n\
                    5   -- more"
                    column_side_a = base_side_a + " binary rpm package"
                    rpm_name_info = {
                        column_side_a: explan
                    }
                    value = [rpm_name_info] + sorted(value, key=operator.itemgetter(CMP_TYPE, column_side_a))
                elif node == CMP_TYPE_DIFFERENCES:
                    for details_name in ALL_DETAILS_NAME:
                        if details_name not in headers:
                            headers = list(headers)
                            headers.append(details_name)

                export.create_csv_report(headers, value, report_path)
            else:
                # eg: node just a single rpm-requires result
                export_single_report(node, value, root_path, osv_title)
        all_rpm_report = os.path.join(export_floder, 'all-rpm-report.csv')
        if os.path.exists(all_rpm_report):
            # genrate single_calculate report.
            single_calculate = IndividualStatistics(all_rpm_report)
            single_calculate.run_statistics(count_abi)
            # generate similar_calculate_result report.
            calculate_similarity(all_rpm_report)
        else:
            logger.info(f"Report: {os.path.basename(all_rpm_report)} not exists! unable to generate calculate report.")
        logger.info(
            f"all results have compare done, please check: {os.path.join(os.path.realpath(root_path), osv_title)}")
        logger.info(f"all similatity are: {similarity}")

        return osv_title


def format_base_side(cmp_side_a, cmp_side_b, iso_path):
    # rpm单包比较结果
    if cmp_side_a.endswith('.src.rpm') and cmp_side_b.endswith('.src.rpm'):
        return os.path.basename(iso_path[0]), os.path.basename(iso_path[1])
    # 远端repo比较结果
    elif 'repodata' in cmp_side_a and 'repodata' in cmp_side_b:
        side_a = cmp_side_a.split(',')[0]
        side_b = cmp_side_b.split(',')[0]
        return side_a.split('://')[-1], side_b.split('://')[-1]
    # iso比较结果
    else:
        return cmp_side_a, cmp_side_b


def get_title(base_side):
    if not base_side.endswith('.iso'):
        if '/' in base_side:
            base_side = base_side.replace('/', '-').strip('-')
        return base_side

    title = base_side.split('.')[:-1]
    return '-'.join(title)


def save_detail_result(file_path, content):
    flags = os.O_RDWR | os.O_CREAT
    modes = stat.S_IROTH | stat.S_IRWXU
    with os.fdopen(os.open(file_path, flags, modes), 'w', encoding='utf-8') as fd:
        fd.write(content)


def export_single_report(node, single_result, root_path, osv_title):
    for cmp_type, results in single_result.items():
        # for single result export, we should skip base level compare. like:
        # rpm, repository, ...
        if cmp_type in COMPOSITE_CMPS:
            continue

        report_path = export.create_directory(root_path, node.replace(' ', '-'), osv_title, cmp_type)
        headers = results[0].keys()
        headers = list(headers)
        if cmp_type == CMP_TYPE_DRIVE_KABI and "effect drivers" not in headers:
            headers.append("effect drivers")
        if "details path" not in headers:
            if cmp_type in [CMP_TYPE_SERVICE, CMP_TYPE_RPM_CONFIG, CMP_TYPE_RPM_ABI, CMP_TYPE_RPM_HEADER]:
                headers.append("details path")
        export.create_csv_report(headers, results, report_path)


def parse_result(result, base_side_a, base_side_b, rows, count_abi, report_path, parent_side_a=None, parent_side_b=None,
                 cmp_type=None, detail=None):
    if hasattr(result, 'diff_components') and result.diff_components:
        if result.cmp_type == CMP_TYPE_RPM:
            assgin_composite_result(rows, result, base_side_a, base_side_b, parent_side_a, parent_side_b, count_abi)

        for son_result in result.diff_components:
            parse_result(son_result, base_side_a, base_side_b, rows, count_abi, report_path, result.cmp_side_a,
                         result.cmp_side_b, result.cmp_type, result.detail)
    else:
        if result.cmp_type == CMP_TYPE_RPM_LEVEL:
            assgin_rpm_pkg_result(rows, result, base_side_a, base_side_b)
        else:
            assgin_single_result(rows, result, base_side_a, base_side_b, parent_side_a, parent_side_b, detail,
                                 report_path)


def assgin_end_result(summary_dict):
    if summary_dict.get("1"):
        if summary_dict["1"]["diff"] == 0:
            end_result = "基础兼容"

            if summary_dict.get("2") and summary_dict["2"]["diff"] == 0:
                summary_dict["2"]["result"] = "深度兼容"
                end_result = "深度兼容"
        else:
            end_result = "不通过"

        summary_dict["1"]["result"] = end_result

    return sorted(summary_dict.values(), key=lambda i: i["category level"])


def assgin_composite_result(rows, result, side_a, side_b, parent_side_a, parent_side_b, count_abi):
    side = result.cmp_side_b if result.cmp_side_b else result.cmp_side_a
    category_level = result.detail
    count_results = result.count_result
    compare_type = result.diff_components[0].cmp_type
    second_path = get_second_path(compare_type)
    compare_detail = ' ' + second_path + '/' + side + '.csv ' if side else ''

    row = {
        side_a + " binary rpm package": result.cmp_side_a,
        side_a + " source package": parent_side_a,
        side_b + " binary rpm package": result.cmp_side_b,
        side_b + " source package": parent_side_b,
        "compare result": result.cmp_result,
        "compare detail": compare_detail,
        "compare type": compare_type,
        "category level": category_level,
        "same": "N/A",
        "more": "N/A",
        "less": "N/A",
        "diff": "N/A"
    }
    if hasattr(result, 'count_result'):
        row["same"] = count_results['same']
        row["more"] = count_results['more']
        row["less"] = count_results['less']
        row["diff"] = count_results['diff']
    rows.setdefault(result.cmp_type, [])
    rows[result.cmp_type].append(row)

    if compare_type == CMP_TYPE_RPM_ABI and result.cmp_result == CMP_RESULT_DIFF and hasattr(result, 'count_result'):
        for i, type_abi in enumerate(COUNT_ABI_DETAILS):
            count_abi["all_packages_abi"][i] += count_results[type_abi]
        if category_level == 1:
            for i, type_abi in enumerate(COUNT_ABI_DETAILS):
                count_abi["l1_packages_abi"][i] += count_results[type_abi]
        elif category_level == 2:
            for i, type_abi in enumerate(COUNT_ABI_DETAILS):
                count_abi["l2_packages_abi"][i] += count_results[type_abi]


def assgin_single_result(rows, result, base_side_a, base_side_b, parent_side_a, parent_side_b, detail, report_path):
    parent_side = parent_side_b if parent_side_b else parent_side_a
    if result.cmp_type == CMP_TYPE_RPM_REQUIRES:
        row = {
            "binary rpm package": parent_side,
            base_side_a + " symbol name": result.cmp_side_a.get('name', '') if result.cmp_side_a else '',
            base_side_a + " package name": result.cmp_side_a.get('packages', '') if result.cmp_side_a else '',
            base_side_a + " dependence type": result.cmp_side_a.get('dependence', None) if result.cmp_side_a else None,
            base_side_b + " symbol name": result.cmp_side_b.get('name', '') if result.cmp_side_b else '',
            base_side_b + " package name": result.cmp_side_b.get('packages', '') if result.cmp_side_b else '',
            base_side_b + " dependence type": result.cmp_side_b.get('dependence', None) if result.cmp_side_b else None,
            "compare result": result.cmp_result,
            "compare type": result.cmp_type,
        }
    else:
        row = {
            "binary rpm package": parent_side,
            "Base__" + base_side_a: result.cmp_side_a.strip(),
            "Check__" + base_side_b: result.cmp_side_b.strip(),
            "compare result": result.cmp_result,
            "compare type": result.cmp_type,
        }
    if result.cmp_type == CMP_TYPE_SERVICE_DETAIL:
        if detail:
            row["file_name"] = detail.get("file_name")
    else:
        row["category level"] = detail
        if result.cmp_type == CMP_TYPE_DRIVE_KABI:
            row["effect drivers"] = result.detail
        elif result.cmp_type == CMP_TYPE_SERVICE:
            row["details path"] = result.detail
    # handle kabi result

    rows.setdefault(parent_side, {})
    rows[parent_side].setdefault(result.cmp_type, [])
    rows[parent_side][result.cmp_type].append(row)
    if result.detail_file:
        dir_path = os.path.join(report_path, DETAIL_PATH, result.cmp_type.split()[-1], parent_side_b)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        file_a = os.path.basename(result.cmp_side_a)
        file_b = os.path.basename(result.cmp_side_b)
        file_path = os.path.join(dir_path, f'{file_a}__cmp__{file_b}_{uuid.uuid4().clock_seq}.md')
        row["details path"] = DETAIL_PATH + file_path.split(DETAIL_PATH)[-1]
        save_detail_result(file_path, result.detail_file)


def assgin_rpm_pkg_result(rows, result, base_side_a, base_side_b):
    category_level = result.detail['category']
    row = {
        base_side_a + " binary rpm package": result.cmp_side_a,
        base_side_a + " source package": result.detail['source_package_a'],
        base_side_b + " binary rpm package": result.cmp_side_b,
        base_side_b + " source package": result.detail['source_package_b'],
        "compare result": result.cmp_result,
        "compare detail": '',
        "compare type": result.cmp_type,
        "category level": category_level,
        "same": 'N/A',
        "more": 'N/A',
        "less": 'N/A',
        "diff": 'N/A'
    }

    # add rpm_pkg_result to rpm list
    rows.setdefault(CMP_TYPE_RPM, [])
    rows[CMP_TYPE_RPM].append(row)


def get_differences_info(rows):
    differences_info = []
    if not rows:
        return []
    for key in rows.keys():
        if key.endswith('.rpm') and not key.endswith('.src.rpm'):
            for cmp_type, results in rows[key].items():
                for single_result in results:
                    if single_result['compare result'] != CMP_RESULT_SAME:
                        if cmp_type == CMP_TYPE_RPM_REQUIRES:
                            single_result = get_require_differencs_info(single_result)
                        differences_info.append(single_result)
    return differences_info


def get_require_differencs_info(single_result):
    differencs_info = {'binary rpm package': single_result['binary rpm package']}
    result_keys = list(single_result.keys())
    side_a = "Base__" + result_keys[1].split(" ")[0]
    side_b = "Check__" + result_keys[4].split(" ")[0]
    symbol_a, package_a = single_result.get(result_keys[1]), single_result.get(result_keys[2])
    symbol_b, package_b = single_result.get(result_keys[4]), single_result.get(result_keys[5])
    differencs_info[side_a] = None if not symbol_a and not package_a else symbol_a.strip() + "  [" + package_a + "]"
    differencs_info[side_b] = None if not symbol_b and not package_b else symbol_b.strip() + "  [" + package_b + "]"
    differencs_info['compare result'] = single_result['compare result']
    differencs_info['compare type'] = single_result['compare type']
    differencs_info['category level'] = single_result['category level']

    return differencs_info
