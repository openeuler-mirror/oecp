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
# Create: 2022-07-05
# Description: json result
# **********************************************************************************
"""
import os
import logging
import re
import json
import time
from tempfile import TemporaryDirectory

import sqlalchemy

from oecp.db.symbol import Symbol
from oecp.db.symbol_temporary import SymbolTemporary
from oecp.db.pull_request import PullRequest
from oecp.proxy.rpm_proxy import RPMProxy
from oecp.result.constants import ALL_ARCH, OPENEULER, BRANCH_LEN
from oecp.symbol_analyze.controller.symbol_analyze import RpmController
from oecp.utils.shell import shell_cmd
from oecp.utils import common

logger = logging.getLogger('oecp')


class RpmAnalyze(object):
    def __init__(self, args, repository_old, repository_new):
        self.branch_name = args.symbol
        self.work_dir = self.get_work_dir(args.work_dir)
        self.pr_id = args.pr_id
        self.repository_old = repository_old
        self.repository_new = repository_new
        self.split_flag = '__rpm__'
        self.password = args.databse_password

    @staticmethod
    def get_work_dir(work_dir):
        if not os.path.exists(work_dir):
            os.makedirs(work_dir)
        return work_dir

    def submit_symbol_change(self):
        for arch in ALL_ARCH:
            branch_arch = '-'.join([self.branch_name, arch])
            database_name = cut_database_name(branch_arch)
            logger.info(f"Start writing symbols to the {database_name} database...")
            rpm_controller = RpmController(database_name, self.password)
            pr_mappings = rpm_controller.query_pr_mappings_by_pr_id(self.pr_id)
            pr_rpms_old = [pr.rpm_name for pr in pr_mappings if not pr.is_rpm_new]
            pr_rpms_new = [pr.rpm_name for pr in pr_mappings if pr.is_rpm_new]
            logger.info(
                f"Query previous version RPMS: {','.join(pr_rpms_old)}\nNext version RPMS: {','.join(pr_rpms_new)}")
            for pr in pr_mappings:
                if not pr.is_rpm_new:
                    rpm_controller.bulk_delete_datas(Symbol, pr.rpm_name)
            for pr in pr_mappings:
                if pr.is_rpm_new:
                    tmp_symbols = rpm_controller.query_tmp_symbol({'rpm_name': pr.rpm_name})
                    for symbol in tmp_symbols:
                        rpm_controller.set_symbols(
                            Symbol(rpm_name=symbol.rpm_name, so_name=symbol.so_name,
                                   u_symbol_table=symbol.u_symbol_table,
                                   association_so_name=symbol.association_so_name))
                    rpm_controller.bulk_delete_datas(SymbolTemporary, pr.rpm_name)
            rpm_controller.bulk_save_symbols(Symbol)
            rpm_controller.delete_pr_mapping_by_pr_id(self.pr_id)
            logger.info(f'Submit database {database_name} symbol changed done')

    def construct_database(self, is_tmp_table=False):
        database_name = cut_database_name(self.branch_name)
        try:
            rpm_controller = RpmController(database_name, self.password)
        except sqlalchemy.exc.OperationalError as err:
            logger.warning(f"connect to mysql server faild, {err}\nwait for 2 minutes to connect again..")
            time.sleep(120)
            rpm_controller = RpmController(database_name, self.password)
        if is_tmp_table:
            model = SymbolTemporary
            pr_mappings = rpm_controller.query_pr_mappings_by_pr_id(self.pr_id)
            logger.info(
                f"Total query {len(pr_mappings)} pr_mapping result from database {database_name} table pull_request")
            for pr in pr_mappings:
                if pr.is_rpm_new:
                    rpm_controller.bulk_delete_datas(SymbolTemporary, pr.rpm_name)
            rpm_controller.delete_pr_mapping_by_pr_id(self.pr_id)
            for rpm_name, repository in self.repository_old.items():
                rpm_path = repository[rpm_name]['path']
                rpm = os.path.basename(rpm_path)
                rpm_controller.set_pr_mapping(PullRequest(pr_id=self.pr_id, rpm_name=rpm, is_rpm_new=False))
            for rpm_name, repository in self.repository_new.items():
                rpm_path = repository[rpm_name]['path']
                rpm = os.path.basename(rpm_path)
                rpm_controller.set_pr_mapping(PullRequest(pr_id=self.pr_id, rpm_name=rpm, is_rpm_new=True))
            rpm_controller.bulk_save_pr_mappings(self.pr_id)
        else:
            model = Symbol
        for rpm_name, repository in self.repository_new.items():
            rpm_path = repository[rpm_name]['path']
            rpm = os.path.basename(rpm_path)
            if rpm_path:
                extract_dir_obj = self.rpm_to_cpio(rpm_path)
                all_files = common.search_elf_files(extract_dir_obj.name)
                if all_files:
                    try:
                        self.construct_symbol_structures(rpm_controller, all_files, rpm, model)
                    except Exception as e:
                        logger.error(f'construct database error: {e}')
                else:
                    logger.debug(f'{rpm} does not have binary or so.')

        rpm_controller.bulk_save_symbols(model)

    def construct_symbol_structures(self, rpm_controller, binary_files, rpm_name, model):
        data_number = 0
        for binary_file in binary_files:
            all_require_so = self.collect_required_so(binary_file)
            out_symbols = self.collect_symbols(binary_file)
            if out_symbols:
                for out_symbol in out_symbols:
                    rpm_controller.set_symbols(
                        model(rpm_name=rpm_name, so_name=os.path.basename(binary_file), u_symbol_table=out_symbol,
                              association_so_name=json.dumps(all_require_so)))
            data_number += len(out_symbols)
        logger.debug(f'Number of {rpm_name} construct symbol data: {data_number}')

    def rpm_to_cpio(self, rpm_path):
        full_path = os.path.realpath(rpm_path)
        pwd_path = os.getcwd()
        verbose_path = os.path.basename(rpm_path)
        extract_dir_obj = TemporaryDirectory(suffix='__rpm__', prefix=f'_{verbose_path}_', dir=self.work_dir)
        extract_dir_name = extract_dir_obj.name
        os.chdir(extract_dir_name)
        RPMProxy.perform_cpio(full_path)
        os.chdir(pwd_path)

        return extract_dir_obj

    def collect_symbols(self, so_file):
        out_symbols = []
        cmd = "nm -D {} -u ".format(so_file)
        ret, out, err = shell_cmd(cmd.split())
        if not ret and out:
            for symbol in out.split('\n'):
                if symbol:
                    out_symbols.append(symbol.split()[-1])
        out_symbols = set(out_symbols)
        logger.debug(f"{so_file.split('__rpm__')[-1]} has {len(out_symbols)} out symbols.")
        return out_symbols

    def collect_required_so(self, file):
        all_needed_so = []
        cmd = f"readelf -d {file}"
        ret, out, err = shell_cmd(cmd.split())
        if not ret and out:
            for line in out.split("\n"):
                pattern = r"(NEEDED).*\[(.*)]"
                so_file = re.search(pattern, line)
                if so_file:
                    all_needed_so.append(so_file.group(2))
        if all_needed_so:
            return all_needed_so
        else:
            return None


def cut_database_name(database_name):
    """
    截取超过64个字符的分支名，创建数据库
    @param database_name: eg:Multi-Version_NestOS-For-Container_openEuler-22.03-LTS-SP3-x86_64
    @return:
    """
    if len(database_name) > BRANCH_LEN:
        database_name = re.sub(OPENEULER + '-', '', database_name)
    if len(database_name) > BRANCH_LEN:
        return database_name[-64:]

    return database_name
