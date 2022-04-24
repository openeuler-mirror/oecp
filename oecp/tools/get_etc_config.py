import os
import platform
import sys
import json

path_lists = []


def list_dir(file_dir):
    '''
        通过 listdir 得到的是仅当前路径下的文件名，不包括子目录中的文件，如果需要得到所有文件需要递归
    '''
    # print ('\n\n<><><><><><> listdir <><><><><><>')
    # print ("current dir : {0}".format(file_dir))
    dir_list = os.listdir(file_dir)
    for cur_file in dir_list:
        # 获取文件的绝对路径
        path = os.path.join(file_dir, cur_file)
        if os.path.isfile(path):  # 判断是否是文件还是目录需要用绝对路径
            file_name = os.path.basename(path)
            if is_config(file_name): 
                print("file name:{0}".format(file_name))
                path_lists.append(path)
        if os.path.isdir(path):
            list_dir(path)   # 递归子目录
    # print (path_lists)
    return path_lists


def is_readable(path):
    '''
    Check if a given path is readable by the current user.
    :param path: The path to check
    :returns: True or False
    '''
    if os.access(path, os.F_OK) and os.access(path, os.R_OK):
     # The path exists and is readable
        return True
    # The path does not exist
    return False


def is_mysql_config(file_name):
    if 'mysql' in file_name or file_name == 'my.cnf':
        return True
    else:
        return False


def is_config(file_name):
    if file_name.endswith("cnf") or file_name.endswith("conf"):
        return True
    return False


def read_file(file_path):
    if is_readable(file_path):
        with open(file_path, "r") as f:
            result = f.readlines(2)
            print(result)


def machine():
    """Return type of machine."""
    if os.name == 'nt' and sys.version_info[:2] < (2, 7):
        return os.environ.get("PROCESSOR_ARCHITEW6432", os.environ.get('PROCESSOR_ARCHITECTURE', ''))
    else:
        return platform.machine()


def os_bits(machine = machine()):
    """Return bitness of operating system, or None if unknown."""
    machine2bits = {'AMD64': 64, 'x86_64': 64, 'i386': 32, 'x86': 32}
    return machine2bits.get(machine, None)


def format_config(paths):
    json_dict = {}
    # all_details = {}
    for file_name in paths:
        basename = os.path.basename(file_name)
        item = {}
        detail = {}
        with open(file_name, "r") as f:
            for line in f.readlines():
                line = line.strip().replace("\n", "")
                line = line.strip().replace("\t", "")
                if line == "":
                    continue
                if line.startswith("#"):
                    continue
                if '=' in line:
                    name, version = line.split("=", 1)
                    detail.setdefault(name, version)
                    # all_details.setdefault(name,version)
        item.setdefault('filename', basename)
        item.setdefault('path', file_name)
        item.setdefault('data', detail)
        json_dict.setdefault(file_name, item)
    # all_datas = {'filename':'all','path':'none','data':all_details}
    # json_dict.setdefault('allfile',all_datas)
    json_datas = json.dumps(json_dict, indent=4, separators=(',', ': '))
    return json_datas


def write_file(json_file_name, datas):
    json_file_path = "/home/{}.json".format(json_file_name)
    f = open(json_file_path, 'w')
    f.write(datas)
    f.close()


if __name__ == '__main__':
    path_lists = list_dir('/etc')
    json_file_name = platform.platform(True)
    json_datas = format_config(path_lists)
    write_file(json_file_name, json_datas)
