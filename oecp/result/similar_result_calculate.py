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
# Create: 2022-06-10
# Description: compare result
# **********************************************************************************
"""
import os.path
import pandas as pd


def calculate_similarity(all_rpm_report):
    df = pd.read_csv(all_rpm_report)
    first_colomn_name = df.columns.tolist()[0]

    df.drop(labels=0, inplace=True)
    df.fillna('', inplace=True)

    # 新增两列包名
    package_name_list = []
    for source_package in list(df[first_colomn_name]):
        if source_package != '':
            package_name_list.append(source_package.rsplit(".", 2)[0].rsplit("-", 2)[0])
        else:
            package_name_list.append('')
    df['first_package_name_list'] = package_name_list

    # 软件包交集数量
    common_rpm_list = df[
        (df['compare result'] == '1') | (df['compare result'] == '1.1') | (df['compare result'] == '2') | (
                df['compare result'] == '3')]
    # centos软件包数量(去除4选项，即前者有，后者无)
    centos_rpm_list = df[
        (df['compare result'] == '1') | (df['compare result'] == '1.1') | (df['compare result'] == '2') | (
                df['compare result'] == '3')
        | (df['compare result'] == '5')]
    # 软件包总数
    total_rmp_list = df[
        (df['compare result'] == '1') | (df['compare result'] == '1.1') | (df['compare result'] == '2') | (
                df['compare result'] == '3')
        | (df['compare result'] == '4') | (df['compare result'] == '5')]

    # part 2
    result_dict = {}
    all_src_name_key = list(common_rpm_list[first_colomn_name])
    soft_package_table = df[(df['compare result'] != '4') | (df['compare result'] != '5')]

    temp_simple_reslut = [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0]
    ]

    for package in all_src_name_key:
        tmp_table = soft_package_table[soft_package_table[first_colomn_name] == package]
        tmp_require = tmp_table[tmp_table["compare type"] == "rpm requires"]
        tmp_provide = tmp_table[tmp_table["compare type"] == "rpm provides"]
        has_require = True
        if (len(list(tmp_require["compare type"])) == 0 and len(list(tmp_provide["compare type"])) == 0):
            has_require = False
        tmp_list = list(tmp_table['compare result'])
        divisor = len(tmp_list) - 1
        if divisor:
            if '1' in tmp_list:
                result_dict[package] = 1
                temp_simple_reslut[0][0] += 1
                temp_simple_reslut[0][1] += round(tmp_list.count('same') / divisor, 2)
                temp_simple_reslut[0][2] += list(tmp_require["compare result"]).count("same")
                temp_simple_reslut[0][3] += list(tmp_provide["compare result"]).count("same")
                temp_simple_reslut[0][4] += 1 if has_require else 0
            elif '1.1' in tmp_list:
                result_dict[package] = 0.7 + round(tmp_list.count('same') / divisor, 2) * 0.3
                temp_simple_reslut[1][0] += 1
                temp_simple_reslut[1][1] += round(tmp_list.count('same') / divisor, 2)
                temp_simple_reslut[1][2] += list(tmp_require["compare result"]).count("same")
                temp_simple_reslut[1][3] += list(tmp_provide["compare result"]).count("same")
                temp_simple_reslut[1][4] += 1 if has_require else 0
            elif '2' in tmp_list:
                result_dict[package] = 0.3 + round(tmp_list.count('same') / divisor, 2) * 0.7
                temp_simple_reslut[2][0] += 1
                temp_simple_reslut[2][2] += list(tmp_require["compare result"]).count("same")
                temp_simple_reslut[2][3] += list(tmp_provide["compare result"]).count("same")
                require_provide_num = temp_simple_reslut[2][2] + list(tmp_require["compare result"]).count("diff") \
                                      + temp_simple_reslut[2][3] + list(tmp_provide["compare result"]).count("diff")
                same_molecule = tmp_list.count('same') - temp_simple_reslut[2][2] - temp_simple_reslut[2][3]
                dimension_num = divisor - require_provide_num
                if same_molecule != 0 and dimension_num != 0:
                    temp_simple_reslut[2][1] += round(
                        same_molecule
                        / dimension_num, 2
                    )
                temp_simple_reslut[2][4] += 1 if has_require else 0
            elif '3' in tmp_list:
                result_dict[package] = round(tmp_list.count('same') / divisor, 2)
                temp_simple_reslut[3][0] += 1
                temp_simple_reslut[3][1] += round(tmp_list.count('same') / divisor, 2)
                temp_simple_reslut[3][2] += list(tmp_require["compare result"]).count("same")
                temp_simple_reslut[3][3] += list(tmp_provide["compare result"]).count("same")
                temp_simple_reslut[3][4] += 1 if has_require else 0
            else:
                pass

    molecule_section2 = 0
    for i in range(3):
        if i != 2:
            molecule_section2 += temp_simple_reslut[i][0]
        else:
            molecule_section2 += temp_simple_reslut[i][1]

    molecule_section3 = 0
    denominator = 0
    line = 1
    for tmp in temp_simple_reslut:
        if line <= 2:
            molecule_section3 += 2 * tmp[4]
            denominator += tmp[4]
            line += 1
        elif 2 < line < 4:
            molecule_section3 += tmp[2] + tmp[3]
            denominator += tmp[4]
            line += 1
        else:
            denominator += tmp[4]
            line += 1

    section1_result = round(len(common_rpm_list) / len(total_rmp_list) * 100, 2) if not total_rmp_list.empty else 0
    section2_result = round(molecule_section2 / len(common_rpm_list) * 100, 2) if not common_rpm_list.empty else 0
    section3_result = round(molecule_section3 / (2 * denominator) * 100, 2) if denominator else 0
    total_result = round(section1_result * 0.1 + section2_result * 0.6 + section3_result * 0.3, 2)
    total_list = []
    section1_list = ['软件包范围', '10%', '{}%'.format(section1_result)]
    section2_list = ['软件包相似度', '60%', '{}%'.format(section2_result)]
    section3_list = ['软件包依赖关系', '30%', '{}%'.format(section3_result)]
    section4_list = ['合计', '', '{}%'.format(total_result)]
    column = ['测试项', '权重', '单项得分值']
    total_list.append(section1_list)
    total_list.append(section2_list)
    total_list.append(section3_list)
    total_list.append(section4_list)
    result_df = pd.DataFrame(columns=column, data=total_list, )
    result_df.to_csv(os.path.join(os.path.dirname(all_rpm_report), 'similar_calculate_result.csv'), index=False,
                     encoding='utf_8_sig')
