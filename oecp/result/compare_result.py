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
# Author:
# Create: 2021-09-06
# Description: compare result
# **********************************************************************************
"""
import sys
import logging
import uuid

from oecp.excel.create_web_show_result import WebShowResult
from oecp.excel.osv_data_summary import DataExcelFile
from oecp.result import export
from oecp.result.export import get_second_path
from oecp.result.test_result import *
from oecp.result.constants import *
from oecp.result.similarity import *
from oecp.result.json_result import *

logger = logging.getLogger("oecp")


class CompareResultComponent(object):
    """
    比较结果对象
    """

    def __init__(self, cmp_type, cmp_result, cmp_side_a, cmp_side_b, detail=None):
        """

        :param cmp_type: 比较名称，eg：kernel abi，kernel config
        :param cmp_result: 比较结果
        :param cmp_side_a: 比较对象
        :param cmp_side_b: 比较对象
        :param detail: 比较结果详细内容
        """
        self._cmp_type = cmp_type
        self._cmp_result = cmp_result
        self._cmp_side_a = cmp_side_a
        self._cmp_side_b = cmp_side_b
        self._detail = detail
        self._binary_rpm_package = None
        self._source_package = None
        self._level = None

    def set_cmp_type(self, cmp_type):
        """

        :param cmp_type:
        :return:
        """
        self._cmp_type = cmp_type

    def set_binary_rpm_package(self, binary_rpm_package):
        self._binary_rpm_package = binary_rpm_package

    def set_cmp_result(self, cmp_result):
        """
        需要根据叶子节点结果判断父节点结果来设置父节点结果
        @param cmp_result:
        @return:
        """
        self._cmp_result = cmp_result

    def set_source_package(self, source_package):
        self._source_package = source_package

    def set_level(self, level):
        """
        :param level: rpm包的兼容性等级
        """
        self._level = level

    def __str__(self):
        return "{} {} {} {} {}".format(
            self._cmp_type, self._cmp_result, self._cmp_side_a, self._cmp_side_b, self._detail)


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
        self._detail = detail
        self._diff_components = []  # 比较结果对象列表
        self._count_result = count_result

    def add_component(self, *diff_components):
        """

        :param diff_components:
        :return:
        """
        self._diff_components.extend(diff_components)

    def add_count_info(self, count_result):
        self._count_result = count_result

    def set_cmp_result(self, cmp_result=None):
        if cmp_result:
            super(CompareResultComposite, self).set_cmp_result(cmp_result)
            return
        for diff_component in self._diff_components:
            if diff_component._cmp_result == CMP_RESULT_DIFF:
                self._cmp_result = CMP_RESULT_DIFF
                break
        else:
            self._cmp_result = CMP_RESULT_SAME

    def __str__(self):
        """

        :return:
        """
        string = ["{} {} {} {} {}".format(
            self._cmp_type, self._cmp_result, self._cmp_side_a, self._cmp_side_b, self._detail)] + \
                 [str(component) for component in self._diff_components]
        return "\n".join(string)

    def export(self, root_path, baseline, result_format, iso_path):
        base_side_a = self._cmp_side_a
        base_side_b = self._cmp_side_b
        osv_title = 'report-' + get_title(base_side_a) + '-' + get_title(base_side_b)

        # performance_rows = performance_result_parser(base_side_a, base_side_b, root_path, baseline)
        # rpm_test_rows, rpm_test_details = test_result_parser(base_side_a, base_side_b, root_path)

        # all result which need to export as csv
        # eg:
        # {
        #   "rpm": [
        #     result_row1,
        #     ...
        #   ],
        #   "xxx.rpm": {
        #     "rpm require": [
        #       single_result_row1,
        #       ...
        #     ],
        #     ...
        #   },
        #   ...
        # }
        rows = {}
        parse_result(self, base_side_a, base_side_b, rows)
        if result_format == 'json':
            result = json_result(rows, base_side_a, base_side_b)
            export.export_json(root_path, 'osv', osv_title, result)
            logger.info(
                f"all results have compare done, please check: {os.path.join(os.path.realpath(root_path), osv_title)}")
            return 0

        performance_rows = performance_result_parser(base_side_a, base_side_b, root_path, baseline)
        rpm_test_rows, rpm_test_details = test_result_parser(base_side_a, base_side_b, root_path)
        ciconfig_rows, file_config_rows = ciconfig_result_parser(base_side_a, base_side_b, root_path)
        at_rows = at_result_parser(base_side_b, root_path)
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
        args = (similarity, base_side_a, base_side_b, root_path, osv_title, iso_path)
        excel_file.write_summary_file(*args)
        web_show_result = WebShowResult(excel_file.tools_result, excel_file.conclusion)
        web_show_result.write_json_result(*args)
        rows["similarity"] = [similarity]

        summary = assgin_summary_result(rows, base_side_a, base_side_b)
        if summary:
            rows["result"] = summary

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
                    explan = "rpm package name explan:\n\
                    1   -- same name + version + son-version + release num\n\
                    1.1 -- same name + version + son-version\n\
                    2   -- same name + version\n\
                    3   -- same name\n\
                    4   -- less\n\
                    5   -- more"
                    rpm_name_info = {
                        base_side_a + " binary rpm package": explan
                    }
                    value = [rpm_name_info] + value

                export.create_csv_report(headers, value, report_path)
            else:
                # eg: node just a single rpm-requires result
                export_single_report(node, value, root_path, osv_title)
        logger.info(
            f"all results have compare done, please check: {os.path.join(os.path.realpath(root_path), osv_title)}")
        logger.info(f"all similatity are: {similarity}")


def get_title(base_side):
    if not base_side.endswith('.iso'):
        return base_side

    title = base_side.split('.')[:-1]
    return '-'.join(title)


def export_single_report(node, single_result, root_path, osv_title):
    for cmp_type, results in single_result.items():
        # for single result export, we should skip base level compare. like:
        # rpm, repository, ...
        if cmp_type in COMPOSITE_CMPS:
            continue

        uid = str(uuid.uuid4())
        uid = ''.join(uid.split('-'))
        report_path = export.create_directory(root_path, node.replace(' ', '-'), osv_title, cmp_type, uid)
        headers = results[0].keys()
        export.create_csv_report(headers, results, report_path)


def parse_result(result, base_side_a, base_side_b, rows, parent_side_a=None, parent_side_b=None, cmp_type=None,
                 detail=None):
    if hasattr(result, '_diff_components') and result._diff_components:
        if result._cmp_type == CMP_TYPE_RPM:
            assgin_composite_result(rows, result, base_side_a, base_side_b, parent_side_a, parent_side_b)

        for son_result in result._diff_components:
            parse_result(son_result, base_side_a, base_side_b, rows, result._cmp_side_a, result._cmp_side_b,
                         result._cmp_type, result._detail)
    else:
        if result._cmp_type == CMP_TYPE_RPM_LEVEL:
            assgin_rpm_pkg_result(rows, result, base_side_a, base_side_b, result._cmp_side_a, result._cmp_side_b)
        else:
            assgin_single_result(rows, result, base_side_a, base_side_b, parent_side_a, parent_side_b, detail)


def assgin_summary_result(rows, side_a, side_b):
    # eg:
    #   {
    #     "1": {"xxx0_rpm": "same", "xxx1_rpm": "diff", "xxx2_rpm": "less", ... },
    #     "2": {"xxx3_rpm": "same", "xxx4_rpm": "diff", ...},
    #     "3": {"xxx5_rpm": "same", ...
    #   }
    summary = {}
    pkg_name = {
        '1': "same",
        '1.1': "same",
        '2': "same",
        '3': "diff",
        '4': "less",
        '5': "more"
    }
    for rpm in rows.get(CMP_TYPE_RPM, {}):
        level = str(rpm.get("category level")) if rpm.get("category level") else "6"
        summary.setdefault(level, {})
        rpm_name = rpm[side_a + " binary rpm package"] + rpm[side_b + " binary rpm package"]
        cmp_result = rpm["compare result"]
        if rpm["compare type"] == CMP_TYPE_RPM_LEVEL:
            cmp_result = pkg_name.get(cmp_result)

        summary[level].setdefault(rpm_name, "same")
        if summary[level][rpm_name] == "same" and cmp_result:
            summary[level][rpm_name] = cmp_result

    summary_dict = {}
    for k, rpms in summary.items():
        summary_row = {
            "category level": k,
            "same": 0,
            "diff": 0,
            "less": 0,
            "more": 0
        }
        for rpm_name, result in rpms.items():
            summary_row[result] += 1
        summary_dict[k] = summary_row

    return sorted(summary_dict.values(), key=lambda i: i["category level"])


def assgin_end_result(summary_dict):
    end_result = ''
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


def assgin_composite_result(rows, result, side_a, side_b, parent_side_a, parent_side_b):
    side = result._cmp_side_a if result._cmp_side_a else result._cmp_side_b
    category_level = result._detail
    compare_type = result._diff_components[0]._cmp_type
    second_path = get_second_path(compare_type)
    compare_detail = ' ' + second_path + '/' + side + '.csv ' if side else ''

    row = {
        side_a + " binary rpm package": result._cmp_side_a,
        side_a + " source package": parent_side_a,
        side_b + " binary rpm package": result._cmp_side_b,
        side_b + " source package": parent_side_b,
        "compare result": result._cmp_result,
        "compare detail": compare_detail,
        "compare type": compare_type,
        "category level": category_level,
        "more": "N/A",
        "less": "N/A",
        "diff": "N/A"
        }
    if hasattr(result, '_count_result'):
        row["more"] = result._count_result['more_count']
        row["less"] = result._count_result['less_count']
        row["diff"] = result._count_result['diff_count']
    rows.setdefault(result._cmp_type, [])
    rows[result._cmp_type].append(row)


def assgin_single_result(rows, result, base_side_a, base_side_b, parent_side_a, parent_side_b, detail):
    parent_side = parent_side_a if parent_side_a else parent_side_b
    # is_kernel = False
    # if result._cmp_type == CMP_TYPE_KABI or result._cmp_type == CMP_TYPE_KCONFIG:
    #    is_kernel = True
    #    base_side_a = base_side_a + ' ' + '-'.join(parent_side_a.split('-')[:2])
    #    base_side_b = base_side_b + ' ' + '-'.join(parent_side_b.split('-')[:2])

    row = {
        "binary rpm package": parent_side,
        base_side_a: result._cmp_side_a.strip(),
        base_side_b: result._cmp_side_b.strip(),
        "compare result": result._cmp_result,
        "compare type": result._cmp_type,
    }
    if result._cmp_type == CMP_TYPE_SERVICE_DETAIL:
        row["file_name"] = detail.get("file_name")
    else:
        row["category level"] = detail
        if result._cmp_type == CMP_TYPE_RPM_ABI:
            row["abi details"] = ''
            if result._detail:
                row["abi details"] = result._detail
        elif result._cmp_type == CMP_TYPE_DRIVE_KABI:
            row["effect_driver"] = ''
            if result._detail:
                row["effect_driver"] = result._detail
    # handle kabi result
    # if is_kernel:
    #    row.pop("binary rpm package")

    rows.setdefault(parent_side, {})
    rows[parent_side].setdefault(result._cmp_type, [])
    rows[parent_side][result._cmp_type].append(row)


def assgin_rpm_pkg_result(rows, result, base_side_a, base_side_b, parent_side_a, parent_side_b):
    category_level = result._detail['category']
    row = {
        base_side_a + " binary rpm package": result._cmp_side_a,
        base_side_a + " source package": result._detail['source_package_a'],
        base_side_b + " binary rpm package": result._cmp_side_b,
        base_side_b + " source package": result._detail['source_package_b'],
        "compare result": result._cmp_result,
        "compare detail": '',
        "compare type": result._cmp_type,
        "category level": category_level,
        "more": 'N/A',
        "less": 'N/A',
        "diff": 'N/A'
    }

    # single rpm package name report seem useless,
    # because we will merge them to all-rpm-report.csv
    # rows.setdefault(result._cmp_type, [])
    # rows[result._cmp_type].append(row)

    # add rpm_pkg_result to rpm list
    rows.setdefault(CMP_TYPE_RPM, [])
    rows[CMP_TYPE_RPM].append(row)


def compare_result_name_to_attr(name):
    """
    plan中的compare_type对应的属性变量
    :param name:
    :return:
    """
    return getattr(sys.modules[__name__], name)
