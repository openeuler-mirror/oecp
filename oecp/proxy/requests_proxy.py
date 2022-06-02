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
# Create: 2021-09-03
# Description: requests api proxy
# **********************************************************************************
"""

import logging
import sys
import traceback
from time import time
from urllib.request import urlretrieve
from urllib.error import URLError

from tqdm import tqdm

from oecp.utils.unit_convert import convert_bytes

logger = logging.getLogger("oecp")


def do_download(url, file_path, progress=False, step=1):
    """
    从url下载，保存到file_path
    :param url: 远程地址
    :param file_path: 文件路径
    :param progress: 展示下载进度
    :param step: 每次展示进度步数
    :return:
    """
    def current_timestamp():
        """
        当前秒
        :return:
        """
        return int(time())

    class ReportHook(object):
        """
        回调类
        """
        last_block = 0
        download = 0
        total = 0
        percent = 0
        last_time = current_timestamp()

        def cb(self, block_num=1, block_size=1, total_size=None):
            """
            retrieve reporthook
            :param block_num: 块编号
            :param block_size: 块大小
            :param total_size: 总下载大小
            :return:
            """
            if not total_size:
                return

            self.total = total_size

            download = (block_num - self.last_block) * block_size
            now = current_timestamp()
            interval = now - self.last_time
            if not interval:
                return
            speed = download // interval
            if not speed:
                return

            self.download += download
            percent = self.download * 100 // self.total
            est = (self.total - self.download) // speed

            if percent >= self.percent + step:
                sys.stderr.write(f"{percent}% [{convert_bytes(self.download)}/{convert_bytes(self.total)}] complete, "
                                 f"estimate to take another {est} seconds\n")
                self.percent = percent

            self.last_block = block_num
            self.last_time = now

    #logger.debug("recommended to use requests.proxy.do_download_tqdm instead if stdout support \"\\r\"")
    reporthook = ReportHook().cb if progress else None
    try:
        logger.debug(f"download {url} to {file_path}")
        return urlretrieve(url, file_path, reporthook=reporthook)
    except:
        logger.debug(f"urlretrieve {url} exception {traceback.format_exc()}")


def do_download_tqdm(url, file_path):
    """
    使用tqdm展示下载进度条
    :param url:
    :param file_path:
    :return:
    """
    class ReportHook(tqdm):
        """
        回调类
        """
        last_block = 0

        def cb(self, block_num=1, block_size=1, total_size=None):
            """
            retrieve reporthook
            :param block_num: 块编号
            :param block_size: 块大小
            :param total_size: 总下载大小
            :return:
            """
            if total_size:
                self.total = total_size

            self.update((block_num - self.last_block) * block_size)
            self.last_block = block_num

    with ReportHook(unit='iB', unit_scale=True) as progress_bar:
        try:
            logger.debug(f"download {url} to {file_path}")
            return urlretrieve(url, file_path, progress_bar.cb)
        except:
            logger.debug(f"urlretrieve {url} exception {traceback.format_exc()}")
