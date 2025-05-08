import subprocess
import os
import signal
import hashlib
import logging
from os.path import getsize
logger = logging.getLogger('oecp')


SHELL_ENV = {
        'LANG': 'en_US.UTF-8',
        'PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/bin:/sbin'
    }


def get_md5(file_name):
    fb = open(file_name, 'rb')
    md5 = hashlib.md5()
    while True:
        buf = fb.read(8192)
        if not buf:break
        md5.update(buf)
    fb.close()
    file_md5 = md5.digest()
    return file_md5


def find_dupes(files):
    record = {}
    dup = {}
    for file_name in files:
        compound_key = (getsize(file_name), get_md5(file_name))
        if compound_key in record:
            dup[file_name] = record[compound_key]
        else:
            record[compound_key]=file_name
    return dup


def remove_duplicate_files(file_list):
    duplicate_files = find_dupes(file_list)
    for file_name in duplicate_files.keys():
        file_list.remove(file_name)
    return file_list


def run_cmd(cmd, timeout=None):
    p1 = subprocess.Popen(cmd[0], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(cmd[1], stdin=p1.stdout, stdout=subprocess.PIPE)
    p3 = subprocess.Popen(cmd[2], stdin=p2.stdout, stdout=subprocess.PIPE)

    result, error = p3.communicate(timeout=timeout)
    if p3.returncode != 0:
        if p3.returncode != 1:
            logger.error(f'command execute ERROR,Because:{error}')
        return ""

    return result.decode("utf-8", errors="ignore")


def search_elf_files(tmp_file_path):
    elf_files = []
    get_all_file_info_cmd = [
        ['find', tmp_file_path, '-type', 'f', '-exec', 'file', '{}', '+'],
        ['grep', 'dynamically linked'],
        ['grep', '64-bit']
    ]
    lines = run_cmd(get_all_file_info_cmd).split('\n')[:-1]

    for line in lines:
        elf_files.append(line.split(':')[0])

    return elf_files
