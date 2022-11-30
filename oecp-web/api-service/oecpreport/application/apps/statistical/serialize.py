#!/usr/bin/python3
from marshmallow import Schema
from application.models.report import (
    InterfaceChange,
    ReportChangeInfo,
    Kernel,
    RpmfileAnalyse,
)


class ReportChangeInfo_Schema(Schema):
    """
    报告变化信息
    """

    class Meta:
        model = ReportChangeInfo
        fields = (
            "r_delete",
            "r_add",
            "r_release",
            "version_update",
            "consistent",
            "provide_change",
            "require_change",
            "level",
        )


class ReportInterfaceChange_Schema(Schema):
    """
    报告的接口、结构体、参数等变化
    """

    class Meta:
        model = InterfaceChange
        fields = (
            "interface_change",
            "interface_add",
            "interface_del",
            "param_change",
            "struct_change",
            "struct_del",
            "struct_add",
            "level",
        )


class ServiceCmdConf_Schema(Schema):
    """
    rpm的service 命令 配置
    """

    class Meta:
        model = RpmfileAnalyse
        fields = (
            "rpm_type",
            "rpm_level",
            "package_change",
            "file_more",
            "file_less",
            "file_consistent",
            "file_content_change",
        )


class Rpmfile_Analyse_Schema(Schema):
    """
    文件统计
    """
    class Meta:
        model = RpmfileAnalyse
        fields = (
            "rpm_type",
            "rpm_level",
            "package_change",
            "file_more",
            "file_less",
            "file_consistent",
            "file_content_change"
        )
        
        
class KernelAnalyse_Schema(Schema):
    """
    KernelAnalyse
    """
    class Meta:
        model = Kernel
        fields = (
            "kernel_analyse",
            "more",
            "less",
            "same",
            "diff"
        )