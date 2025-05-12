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
# Description: compare plan
# **********************************************************************************
"""
import glob
import json
import logging
import os
import random
import re
import sys
import time

import yaml

PRJ_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PRJ_PATH not in sys.path:
    sys.path.insert(0, PRJ_PATH)
    
from oecp.utils.shell import shell_cmd
from oecp.compass_ci.parse_result import parse_result
logger = logging.getLogger('oecp')


AARCH64 = 'aarch64'
ARM64 = 'arm64'
AMD64 = 'amd64'
X86_64 = 'x86_64'
X86 = 'x86'
PARAMETERS = 'parameters'
OS_LV = 'os_lv'


class ConnectCompassCI(object):
    def __init__(self, iso_path, job_type='at') -> None:
        super().__init__()
        self._iso_path = iso_path
        self._iso_name = os.path.basename(iso_path)
        self._job_type = job_type.lower()
        self._job_name = ''
        self._run_parameter = {}
        self._arch = 'aarch64'
        self._iso_to_os_info = {}
        self._os_info_to_iso = {}
        self._submit = ['submit', '-c', '-m']
        self._get_result = ['cci ', 'jobs', '-f', 'result_root']
        self._job_id = ''
        self._lkp_tests_path = ''
        self._init_parameter()

    def _init_parameter(self):
        self._init_iso_os_info()
        self._init_run_paramerter()
        self._init_lkp_tests_path()
        self._init_job_name()
    
    def _init_job_name(self):
        job = self._run_parameter.get(self._job_type, {})
        self._job_name = os.path.basename(self.get_job_path(job['job'])).split('.')[0]

    def _init_lkp_tests_path(self):
        cmd = ['which', 'submit']
        code, out, err = shell_cmd(cmd)
        if not code:
            if err:
                logger.warning(err)
            if out:
                for line in out.split("\n"):
                    line = line.strip()
                    if line:
                        self._lkp_tests_path = os.path.dirname(os.path.dirname(line))
    
    def _init_iso_os_info(self):
        info_path = os.path.join(PRJ_PATH, 'oecp/conf/AT/os-iso')
        if not os.path.exists(info_path):
            logger.error(f"Map file {info_path} not exists")
            return
        with open(info_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line[0] == '#':
                    continue
                if 'iso' not in line:
                    continue            
                info = line.split()
                os_info = info[0]
                iso_name = info[1]
                self._iso_to_os_info[iso_name] = os_info
                self._os_info_to_iso[os_info] = iso_name
    
    def _init_run_paramerter(self):
        config_path = os.path.join(PRJ_PATH, "oecp/conf/compass-ci.yaml")
        if not os.path.exists(config_path):
            logger.error(f"Config file {config_path} not exists")
            return
        with open(config_path) as f:
            data = f.read()
            self._run_parameter = yaml.safe_load(data)
    
    def submit_job(self, cmd):
        code, out, err = shell_cmd(cmd)
        if not code:
            if err:
                logger.warning(err)
            if out:
                for line in out.split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                    if "query=>" in line:
                        line = line.strip("query=>")
                        try:
                            res = json.loads(line)
                            if 'job_id' in res:
                                self._job_id = res['job_id']
                        except Exception as e:
                            continue

    def submit(self):
        run_parameter = self.get_run_parameter()
        cmd = self._submit + run_parameter
        os_info = self._iso_to_os_info.get(self._iso_name, '')
        if os_info:
            cmd.append(f'os:arch:os_version={os_info}')
        else:
            logger.error(f"OS info error")
            return ''
        print(' '.join(cmd))
        self.submit_job(cmd)
        logger.info(f"Job id {self._job_id}")
        print(self._job_id)
        return self._job_id

    def get_results(self):
        results = {}
        srv_path = ''
        RESULT_EMPTY = 'query results is empty'
        for job_id in self._job_id:
            self._get_result.append(f"id={job_id}")
            cmd = self._get_result
            code, out, err = shell_cmd(cmd)
            if not code:
                if err:
                    logger.warning(err)
                if out:
                    for line in out.split("\n"):
                        line = line.strip()
                        if line == RESULT_EMPTY:
                            logger.error(RESULT_EMPTY)
                        elif re.match('/result', line):
                            srv_path = line
            if os.path.exists(srv_path):
                job_id_path = os.path.join(srv_path, self._job_name)
                res = glob.glob(job_id_path, recursive=True)
                if res:
                    result_path = res[0]
                    if os.path.exists(result_path):
                        srv_result = parse_result(result_path)
                        if srv_result:
                            results.update(srv_result)
        return results

    def config(self):
        pass

    def get_job_path(self, job_name):
        res = os.path.join(self._lkp_tests_path, job_name)
        if os.path.exists(res):
            return res
        return os.path.expanduser(os.path.join('~/lkp-tests', job_name))

    def get_run_parameter(self):
        res = []
        job = self._run_parameter.get(self._job_type, {})
        res.append(self.get_job_path(job['job']))
        if is_aarch64(self._iso_name):
            parameter = job.get(PARAMETERS, {}).get(AARCH64, {})
        elif is_x86_64(self._iso_name):
            parameter = job.get(PARAMETERS, {}).get(X86_64, {})
            if OS_LV in parameter:
                parameter[OS_LV] = f"{time.strftime('%Y%m%d%H%M%S', time.localtime())}{random.randint(0, sys.maxsize)}"
        else:
            logging.warning("unknown iso arch")
        for key, value in parameter.items():
            res.append(f'{key}={value}')
        return res


def is_aarch64(iso_name):
    if AARCH64 in iso_name:
        return True
    if ARM64 in iso_name:
        return True
    return False


def is_x86_64(iso_name):
    if X86_64 in iso_name:
        return True
    if X86 in iso_name:
        return True
    if AMD64 in iso_name:
        return True
    return False


def get_distance(name, key):
    info = name.lower().split(':')
    key = key.lower()
    distance = 0
    for item in info:
        if item in key:
            distance += 1
    return distance


def get_iso_from_os_info(iso_os, key):
    max = 0
    item = ''
    for name in iso_os:
        distance = get_distance(name, key)
        if distance > max:
            max = distance
            item = iso_os[name]
    return item, max

