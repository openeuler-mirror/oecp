#!/usr/bin/python3
from sqlalchemy import Column, Integer, String, DateTime, Text
from libs.sql import DataBase
from . import BaseModel


class AllRpmReport(BaseModel, DataBase.BASE):
    __tablename__ = "all_rpm_report"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_binary_rpm_package = Column(String(200))
    source_src_package = Column(String(200))
    compare_binary_rpm_package = Column(String(200))
    compare_src_package = Column(String(200))
    compare_result = Column(String(500))
    compare_detail = Column(String(500))
    compare_type = Column(String(50))
    category_level = Column(String(50))
    same = Column(String(20))
    more = Column(String(20))
    less = Column(String(20))
    diff = Column(String(20))
    report_base_id = Column(Integer)


class InterfaceChange(BaseModel, DataBase.BASE):
    __tablename__ = "interface_change"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_base_id = Column(Integer)
    interface_change = Column(String(20))
    interface_add = Column(String(20))
    interface_del = Column(String(20))
    param_change = Column(String(20))
    struct_change = Column(String(20))
    struct_del = Column(String(20))
    struct_add = Column(String(20))
    level = Column(String(10))


class OsvTechnicalReport(BaseModel, DataBase.BASE):
    __tablename__ = "osv_technical_report"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_base_id = Column(Integer)
    osv_version = Column(String(500))
    architecture = Column(String(200))
    release_addr = Column(String(200))
    checksum = Column(String(200))
    base_home_old_ver = Column(String(200))
    detection_result = Column(String(200))
    detail_json = Column(Text)


class ReportBase(BaseModel, DataBase.BASE):
    __tablename__ = "report_base"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200))
    source_version = Column(String(200))
    target_version = Column(String(200))
    state = Column(String(20))
    create_time = Column(DateTime)


class ReportChangeInfo(BaseModel, DataBase.BASE):
    __tablename__ = "report_change_info"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_base_id = Column(Integer)
    r_delete = Column(String(20))
    r_add = Column(String(20))
    r_release = Column(String(20))
    version_update = Column(String(20))
    consistent = Column(String(20))
    provide_change = Column(String(20))
    require_change = Column(String(20))
    level = Column(String(10))


class ReportDetailBase(BaseModel, DataBase.BASE):
    __tablename__ = "report_detail_base"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rpm_package = Column(String(200))
    source = Column(String(500))
    compare = Column(String(500))
    compare_result = Column(String(50))
    compare_type = Column(String(50))
    category_level = Column(String(20))
    effect_drivers = Column(String(500))
    md_detail_path = Column(String(500))
    detail_path = Column(String(200))
    report_base_id = Column(Integer)


class AbiDifferencesCompare(BaseModel, DataBase.BASE):
    __tablename__ = "abi_differences_compare"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rpm_package = Column(String(200))
    source = Column(String(500))
    compare = Column(String(500))
    compare_result = Column(String(50))
    compare_type = Column(String(50))
    category_level = Column(String(20))
    effect_drivers = Column(String(500))
    detail_path = Column(String(500))
    report_base_id = Column(Integer)


class RpmfileAnalyse(BaseModel, DataBase.BASE):
    __tablename__ = "rpmfile_analyse"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_base_id = Column(Integer)
    rpm_type = Column(String(50))
    rpm_level = Column(String(10))
    package_change = Column(String(50))
    file_more = Column(String(50))
    file_less = Column(String(50))
    file_consistent = Column(String(50))
    file_content_change = Column(String(50))


class Kernel(BaseModel, DataBase.BASE):
    __tablename__ = "kernel"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_base_id = Column(Integer)
    kernel_analyse = Column(String(50))
    more = Column(Integer)
    less = Column(Integer)
    same = Column(Integer)
    diff = Column(Integer)


class MdDetail(BaseModel, DataBase.BASE):
    __tablename__ = "md_detail"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_base_id = Column(Integer)
    detail_path = Column(String(500))
    md_content = Column(Text)


class DiffServiceDetail(BaseModel, DataBase.BASE):
    __tablename__ = "diff_service_detail"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_base_id = Column(Integer)
    rpm_package = Column(String(200))
    source = Column(String(500))
    compare = Column(String(500))
    compare_result = Column(String(50))
    compare_type = Column(String(50))
    file_name = Column(String(500))
    detail_path = Column(String(500))


class RpmRequiresAnaylse(BaseModel, DataBase.BASE):
    __tablename__ = "rpm_requires_analyse"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_base_id = Column(Integer)
    rpm_package = Column(String(200))
    source_symbol_name = Column(Text)
    source_package = Column(Text)
    source_dependence_type = Column(String(20))
    compare_symbol_name = Column(Text)
    compare_package = Column(Text)
    compare_dependence_type = Column(String(20))
    compare_result = Column(String(50))
    compare_type = Column(String(50))
    category_level = Column(String(20))
    detail_path = Column(String(500))
