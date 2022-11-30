from flask.blueprints import Blueprint
from flask_restful import Api
from . import view


__all__ = ["blue_print", "api", "urls"]
blue_print = Blueprint("report", __name__)
api = Api()

urls = [
    # 分页查询对比报告详细信息
    (
        view.AllRpmReportApi,
        "/detail/all-rpm/page/<int:limit>/<int:page>",
    ),
    # 分页查询报告总览信息
    (
        view.ReportOverviewApi,
        "/page/<int:limit>/<int:page>",
    ),
    # 查询OSV技术测评报告
    (
        view.OSVReviewApi,
        "/detail/osv/<int:report_base_id>",
    ),
    # 分页查询所有比对出的差异文件
    (
        view.DifferencesFileApi,
        "/detail/all-differences/page/<int:limit>/<int:page>",
    ),
    # 分页查询比对报告详情
    (
        view.ReportCompageDetailApi,
        "/detail/all-compare/page/<int:limit>/<int:page>",
    ),
    # 分页查询require比对报告详情
    (
        view.ReportCompageRequireDetailApi,
        "/detail/all-compare-require/page/<int:limit>/<int:page>",
    ),
    # 获取比价的iso名称
    (
        view.CompareIsoDiff,
        "/compare/iso-info/<int:report_base_id>",
    ),
    # 获取所有比较类型
    (
        view.AllCompareType,
        "/compare/all-compare-type/<int:report_base_id>",
    ),
    # 获取所有比较结果
    (
        view.AllCompareResult,
        "/compare/all-compare-result/<int:report_base_id>",
    ),
    # 修改报告标题/删除报告
    (
        view.ReportVersionApi,
        "/update-version/<int:report_base_id>",
    ),
    # md文档详情
    (
        view.MdDetailApi,
        "/md-detail/<int:report_base_id>",
    ),
    # diff_service-csv文档详情
    (
        view.DiffServiceCSVDetailApi,
        "/diff-service-csv-detail/page/<int:limit>/<int:page>",
    ),
]
