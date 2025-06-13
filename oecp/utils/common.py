import hashlib
from os.path import getsize


def get_md5(file_name):
    fb = open(file_name, 'rb')
    md5 = hashlib.md5()
    while True:
        buf = fb.read(8192)
        if not buf:
            break
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
            record[compound_key] = file_name
    return dup


def remove_duplicate_files(file_list):
    duplicate_files = find_dupes(file_list)
    for file_name in duplicate_files.keys():
        file_list.remove(file_name)
    return file_list
