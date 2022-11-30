#!/usr/bin/python3
from marshmallow import Schema
from application.models.report import (
    AbiDifferencesCompare,
    AllRpmReport,
    MdDetail,
    OsvTechnicalReport,
    ReportDetailBase,
)


class AllRpmReportPage_Schema(Schema):
    """
    报告详情分页展示
    """

    class Meta:
        model = AllRpmReport
        fields = (
            "id",
            "source_binary_rpm_package",
            "source_src_package",
            "compare_binary_rpm_package",
            "compare_src_package",
            "compare_result",
            "compare_detail",
            "compare_type",
            "category_level",
            "more",
            "less",
            "diff",
            "report_base_id",
        )


class ReportCompareDetailPage_Schema(Schema):
    """
    查询比对报告详情分页展示
    """

    class Meta:
        model = ReportDetailBase
        fields = (
            "id",
            "rpm_package",
            "source",
            "compare",
            "compare_result",
            "compare_type",
            "category_level",
            "md_detail_path",
        )


class ReportCompareRequireDetailPage_Schema(Schema):
    """
    查询比对报告requires详情分页展示
    """

    class Meta:
        model = ReportDetailBase
        fields = (
            "id",
            "rpm_package",
            "source_symbol_name",
            "source_package",
            "source_dependence_type",
            "compare_symbol_name",
            "compare_package",
            "compare_dependence_type",
            "compare_result",
            "compare_type",
            "detail_path",
            "category_level",
        )


class OsvTechnical_Schema(Schema):
    """
    OSV报告信息
    """

    class Meta:
        model = OsvTechnicalReport
        fields = (
            "osv_version",
            "architecture",
            "release_addr",
            "checksum",
            "base_home_old_ver",
            "detection_result",
            "detail_json",
        )


class AbiDiffCompagePage_Schema(Schema):
    """
    abi差异化比对
    """

    class Meta:
        model = AbiDifferencesCompare
        fields = (
            "id",
            "rpm_package",
            "source",
            "compare",
            "compare_result",
            "compare_type",
            "category_level",
            "effect_drivers",
            "detail_path",
        )


class MdDetail_Schema(Schema):
    """
    Md详情展示
    """

    class Meta:
        model = MdDetail
        fields = ("id", "detail_path", "md_content")


class DiffServiceCSVDetail_Schema(Schema):

    """
    diff_service-csv文档详情
    """

    class Meta:
        model = MdDetail
        fields = (
            "id",
            "report_base_id",
            "rpm_package",
            "source",
            "compare",
            "compare_result",
            "compare_type",
            "file_name",
        )
