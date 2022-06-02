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
# **********************************************************************************
"""

import os
import logging
import tempfile
import shutil
import hashlib
import glob
from oecp.dumper.base import ComponentsDumper
from oecp.utils.shell import shell_cmd

logger = logging.getLogger('oecp')

class SensitiveImageDumper(ComponentsDumper):

    def __init__(self, repository, cache=None, config=None):
        super(SensitiveImageDumper, self).__init__(repository, cache, config)
        self._component_key = 'sensitive_image'
        self._tmp = []
        self._target_image = []
        self.init_target_image_md5()


    def init_target_image_md5(self):
        image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'conf', 'image'))
        image_list = find_all_images(image_path)
        
        for image in image_list:
            md5 = compute_md5(image)
            if md5:
                self._target_image.append(md5)

    def clean(self):
        for tmp_path in self._tmp:
            if os.path.exists(tmp_path):
                shutil.rmtree(tmp_path)

    def dump(self, repository):
        rpm_path = repository['path']
        dump_list = []
        if os.path.exists(rpm_path):
            tmp_path = tempfile.mkdtemp()
            self._tmp.append(tmp_path)
            cmd = f"cd {tmp_path} && rpm2cpio {rpm_path} | cpio -div"
            os.system(cmd)
            cmd = f"cd {tmp_path} && find . -name *.tar.gz | xargs -r tar -xf"
            os.system(cmd)
            cmd = f"cd {tmp_path} && find . -name *.tar.xz | xargs -r tar -xf"
            os.system(cmd)
            images = find_all_images(tmp_path)            
            for image in images:
                if not image:
                    continue
                md5 = compute_md5(image)
                if md5:
                    if md5 in self._target_image:
                        dump_list.append(image.strip(tmp_path))
        item = {'rpm': os.path.basename(rpm_path), 'kind': self._component_key, 'data': dump_list}
        item.setdefault('category', repository['category'].value)
        return item

    def run(self):
        dumper_list = []
        for _, repository in self.repository.items():
            dumper = self.dump(repository)
            dumper_list.append(dumper)
        return dumper_list


def find_all_images(image_path):
    target_image_path = os.path.abspath(os.path.join(image_path, '**', '*.png'))
    image_list = glob.glob(target_image_path, recursive=True)
    target_image_path = os.path.abspath(os.path.join(image_path, '**', '*.jpg'))
    image_list += glob.glob(target_image_path, recursive=True)     
    return image_list


def compute_md5(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            data = f.read()
            md5 = hashlib.md5(data).hexdigest()
            return md5
    else:
        logger.error((f'file {file_path} not exists'))
        return ''        
