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
# Author:
# Create: 2021-09-14
# Description: factory
# **********************************************************************************
"""
import os
import tempfile
import logging

from oecp.main.repository import Repository
from oecp.main.directory import Directory, DistISO, OEDistRepo
from oecp.main.category import Category

from oecp.utils.misc import path_is_remote
from oecp.proxy.requests_proxy import do_download_tqdm
from oecp.proxy.rpm_proxy import RPMProxy
from oecp.proxy.requests_proxy import do_download

logger = logging.getLogger("oecp")


class Factory(object):
    @staticmethod
    def create(file_paths, args, file_type):

        work_dir = args.work_dir
        category = Category(args.category_path)
        if file_type == 'repo':
            logger.info(f"treat {file_paths} as openEuler dist repository")
            return OEDistRepo(file_paths, work_dir, category)
        elif file_type == 'iso':
            logger.info(f"treat {file_paths} as iso")
            return DistISO(file_paths, work_dir, category, True)
        elif file_type == 'dir':
            # directory
            logger.info(f"treat {file_paths} as local directory")
            return Directory(file_paths[0], work_dir, category, False)
        elif file_type != "none":
            raise RuntimeError(f"compare type {file_type} is illegal")

        file_path = file_paths
        if file_path.endswith("iso"):
            # iso type
            verbose_path = os.path.basename(file_path)
            if path_is_remote(file_path):
                logger.info(f"treat {file_path} as remote iso")
                local_path = tempfile.NamedTemporaryFile(suffix=f"_{verbose_path}", dir=work_dir, delete=True).name
                if do_download_tqdm(file_path, local_path) is None:
                    raise FileNotFoundError(f"{file_path} not exist")
                file_path = local_path

            not path_is_remote(file_path) and logger.info(f"treat {file_path} as local iso")

            return DistISO(file_path, work_dir, category)
        elif file_path.endswith("rpm"):
            # rpm type
            verbose_path = os.path.basename(file_path)
            if path_is_remote(file_path):
                logger.info(f"treat {file_path} as remote rpm file")

                local_path = tempfile.NamedTemporaryFile(suffix=f"_{verbose_path}", dir=work_dir, delete=True)
                if do_download_tqdm(file_path, local_path) is None:
                    raise FileNotFoundError(f"{file_path} not exist")
                file_path = local_path

            not path_is_remote(file_path) and logger.info(f"treat {file_path} as local rpm file")
            name = RPMProxy.rpm_name(verbose_path)
            repository = Repository(work_dir, name, category)
            repository.upsert_a_rpm(file_path, verbose_path)

            return repository

        if path_is_remote(file_path):

            # dist repo
            logger.info(f"treat {file_path} as openEuler dist repository")
            return OEDistRepo([file_path], work_dir, category)
        else:
            # directory
            logger.info(f"treat {file_path} as local directory")

            return Directory(file_path, work_dir, category, False)

    @staticmethod
    def guess_obs_repo(remote_path):
        """
        远程地址存在OS子目录认为是Dist Repo，否则认为是OBS repo
        :param remote_path: 
        :return: 
        """
        with tempfile.NamedTemporaryFile() as f:
            if do_download(f"{remote_path}/OS", f.name):
                return False

        return True
