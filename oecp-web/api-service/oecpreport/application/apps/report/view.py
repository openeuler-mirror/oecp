from flask import request
from sqlalchemy import desc, asc
from sqlalchemy.exc import SQLAlchemyError

from application.apps.base import ApiView
from application.apps.base import dberror
from libs.sql import DataBase
from libs.log import logger
from application.models.report import (
    AbiDifferencesCompare,
    AllRpmReport,
    MdDetail,
    OsvTechnicalReport,
    ReportBase,
    ReportChangeInfo,
    ReportDetailBase,
    RpmRequiresAnaylse,
    DiffServiceDetail,
)
from .serialize import (
    AbiDiffCompagePage_Schema,
    AllRpmReportPage_Schema,
    MdDetail_Schema,
    OsvTechnical_Schema,
    ReportCompareDetailPage_Schema,
    ReportCompareRequireDetailPage_Schema,
    DiffServiceCSVDetail_Schema,
)


class AllRpmReportApi(ApiView):
    """
    分页查询所有rpm对比报告详细信息
    """

    @dberror
    def get(self, page, limit):
        """
        :param page: 当前页
        :param limit: 每页数据大小
        """
        compare_type = request.args.get("compare_type")
        compare_result = request.args.get("compare_result")
        category_level = request.args.get("category_level")
        report_base_id = request.args.get("report_base_id")
        order_by = request.args.get("order_by")
        key_word = request.args.get("key_word")
        order_by_mode = request.args.get("order_by_mode", "asc")
        with DataBase() as db:
            filter_all_rpm_report = db.session.query(AllRpmReport).filter(
                AllRpmReport.report_base_id == report_base_id
            )
            if compare_type:
                filter_all_rpm_report = filter_all_rpm_report.filter(
                    AllRpmReport.compare_type == compare_type
                )
            compare_result_array = compare_result.split("_")
            if compare_result and len(compare_result_array) > 0:
                filter_all_rpm_report = filter_all_rpm_report.filter(
                    AllRpmReport.compare_result.in_(tuple(compare_result_array))
                )
            if category_level:
                filter_all_rpm_report = filter_all_rpm_report.filter(
                    AllRpmReport.category_level == category_level
                )

            if key_word:
                pass
            if all([order_by, order_by_mode]):
                order_by = asc(order_by) if order_by_mode == "asc" else desc(order_by)
                filter_all_rpm_report = filter_all_rpm_report.order_by(order_by)
            total = filter_all_rpm_report.count()
            offset = (page - 1) * limit
            page_data = filter_all_rpm_report.offset(offset).limit(limit).all()
        response_data = {
            "total": total,
            "pages": AllRpmReportPage_Schema(many=True).dump(page_data),
        }
        return self._success_response(data=response_data)


class ReportOverviewApi(ApiView):
    """
    分页查询报告总览信息(对应首页的all l1 l2)
    """

    @property
    def _sql(self):
        return """
        SELECT
            report_change_info.id,
            report_change_info.report_base_id,
            report_change_info.r_delete,
            report_change_info.r_add,
            report_change_info.r_release,
            report_change_info.version_update,
            report_change_info.CONSISTENT as consistent,
            report_change_info.provide_change,
            report_change_info.require_change,
            report_base.title AS version,
            report_base.state AS state 
        FROM
            report_change_info
            LEFT JOIN report_base ON report_change_info.report_base_id = report_base.id 
        WHERE
            report_change_info.`level` =:level
        ORDER BY
            :orderby :order_mode 
            LIMIT :limit OFFSET :offset;
        """

    @dberror
    def get(self, page, limit):
        level = request.args.get("level", "ALL")
        order_by = request.args.get("order_by", "id")
        order_mode = request.args.get("order_by_mode", "asc")
        with DataBase() as db:
            offset = (page - 1) * limit
            report_change_infos = db.session.execute(
                self._sql,
                dict(
                    level=level,
                    offset=offset,
                    limit=limit,
                    orderby=order_by,
                    order_mode=order_mode,
                ),
            )
            total = (
                db.session.query(ReportChangeInfo)
                .filter(ReportChangeInfo.level == level)
                .count()
            )
            page_data = db.to_dict(report_change_infos.fetchall())
        response_data = {
            "total": total,
            "pages": page_data,
        }
        return self._success_response(data=response_data)


class OSVReviewApi(ApiView):
    """
    查询OSV技术测评报告
    """

    @dberror
    def get(self, report_base_id):
        with DataBase() as db:
            osv_report = (
                db.session.query(OsvTechnicalReport)
                .filter(OsvTechnicalReport.report_base_id == report_base_id)
                .first()
            )
        return self._success_response(
            data=OsvTechnical_Schema(many=False).dump(osv_report)
        )


class DifferencesFileApi(ApiView):
    """
    分页查询所有比对出的差异文件
    """

    def get(self, page, limit):
        compare_type = request.args.get("compare_type")
        compare_result = request.args.get("compare_result")
        category_level = request.args.get("category_level")
        report_base_id = request.args.get("report_base_id")
        order_by = request.args.get("order_by")
        key_word = request.args.get("key_word")
        order_by_mode = request.args.get("order_by_mode", "asc")
        with DataBase() as db:
            abi_diff_compare = db.session.query(AbiDifferencesCompare).filter(
                AbiDifferencesCompare.report_base_id == report_base_id,
            )
            if compare_type:
                abi_diff_compare = abi_diff_compare.filter(
                    AbiDifferencesCompare.compare_type == compare_type
                )
            if compare_result:
                abi_diff_compare = abi_diff_compare.filter(
                    AbiDifferencesCompare.compare_result == compare_result
                )
            if category_level:
                abi_diff_compare = abi_diff_compare.filter(
                    AbiDifferencesCompare.category_level == category_level
                )

            if key_word:
                pass
            if all([order_by, order_by_mode]):
                order_by = asc(order_by) if order_by_mode == "asc" else desc(order_by)
                abi_diff_compare = abi_diff_compare.order_by(order_by)
            total = abi_diff_compare.count()
            offset = (page - 1) * limit
            page_data = abi_diff_compare.offset(offset).limit(limit).all()
        response_data = {
            "total": total,
            "pages": AbiDiffCompagePage_Schema(many=True).dump(page_data),
        }
        return self._success_response(data=response_data)


class ReportCompageDetailApi(ApiView):
    """
    分页查询比对报告详情
    """

    @dberror
    def get(self, page, limit):
        compare_type = request.args.get("compare_type")
        compare_result = request.args.get("compare_result")
        category_level = request.args.get("category_level")
        report_base_id = request.args.get("report_base_id")
        order_by = request.args.get("order_by")
        key_word = request.args.get("key_word")
        order_by_mode = request.args.get("order_by_mode", "asc")
        detail_path = request.args.get("path")
        with DataBase() as db:
            filter_compare_report = db.session.query(ReportDetailBase).filter(
                ReportDetailBase.report_base_id == report_base_id
            )
            if detail_path:
                filter_compare_report = filter_compare_report.filter(
                    ReportDetailBase.detail_path == detail_path
                )
            if compare_type:
                filter_compare_report = filter_compare_report.filter(
                    ReportDetailBase.compare_type == compare_type
                )
            compare_result_array = compare_result.split("_")
            if compare_result and len(compare_result_array) > 0:
                filter_compare_report = filter_compare_report.filter(
                    ReportDetailBase.compare_result.in_(tuple(compare_result_array))
                )
            # if compare_result:
            #     filter_compare_report = filter_compare_report.filter(
            #         ReportDetailBase.compare_result == compare_result
            #     )
            if category_level:
                filter_compare_report = filter_compare_report.filter(
                    ReportDetailBase.category_level == category_level
                )

            if key_word:
                pass
            if all([order_by, order_by_mode]):
                order_by = asc(order_by) if order_by_mode == "asc" else desc(order_by)
                filter_compare_report = filter_compare_report.order_by(order_by)
            total = filter_compare_report.count()
            offset = (page - 1) * limit
            page_data = filter_compare_report.offset(offset).limit(limit).all()
        response_data = {
            "total": total,
            "pages": ReportCompareDetailPage_Schema(many=True).dump(page_data),
        }
        return self._success_response(data=response_data)

class ReportCompageRequireDetailApi(ApiView):
    
    """
    分页查询比对报告详情
    """

    @dberror
    def get(self, page, limit):
        compare_type = request.args.get("compare_type")
        compare_result = request.args.get("compare_result")
        category_level = request.args.get("category_level")
        report_base_id = request.args.get("report_base_id")
        order_by = request.args.get("order_by")
        key_word = request.args.get("key_word")
        order_by_mode = request.args.get("order_by_mode", "asc")
        detail_path = request.args.get("path")
        with DataBase() as db:
            filter_compare_report = db.session.query(RpmRequiresAnaylse).filter(
                RpmRequiresAnaylse.report_base_id == report_base_id
            )
            if detail_path:
                filter_compare_report = filter_compare_report.filter(
                    RpmRequiresAnaylse.detail_path == detail_path
                )
            if compare_type:
                filter_compare_report = filter_compare_report.filter(
                    RpmRequiresAnaylse.compare_type == compare_type
                )
            compare_result_array = compare_result.split("_")
            if compare_result and len(compare_result_array) > 0:
                filter_compare_report = filter_compare_report.filter(
                    RpmRequiresAnaylse.compare_result.in_(tuple(compare_result_array))
                )
            if category_level:
                filter_compare_report = filter_compare_report.filter(
                    RpmRequiresAnaylse.category_level == category_level
                )

            if key_word:
                pass
            if all([order_by, order_by_mode]):
                order_by = asc(order_by) if order_by_mode == "asc" else desc(order_by)
                filter_compare_report = filter_compare_report.order_by(order_by)
            total = filter_compare_report.count()
            offset = (page - 1) * limit
            page_data = filter_compare_report.offset(offset).limit(limit).all()
        response_data = {
            "total": total,
            "pages": ReportCompareRequireDetailPage_Schema(many=True).dump(page_data),
        }
        return self._success_response(data=response_data)

class CompareIsoDiff(ApiView):
    """
    对比ISo的差异，主要用于获取比较的基本信息（ISO1 VS ISO2）
    """

    def get(self, report_base_id):
        with DataBase() as db:
            report_base_detail = (
                db.session.query(ReportBase)
                .filter(ReportBase.id == report_base_id)
                .first()
            )

        return self._success_response(
            data=dict(
                source=report_base_detail.source_version,
                target=report_base_detail.target_version,
            )
        )


class AllCompareType(ApiView):
    """获取所有比对类型"""

    def get(self, report_base_id):
        key = request.args.get("key")

        with DataBase() as db:
            table_name = ""
            if key == "detail":
                table_name = "all_rpm_report"
            elif key == "compare":
                table_name = "report_detail_base"
            elif key == "different":
                table_name = "abi_differences_compare"
            elif key == "diffservice":
                table_name = "diff_service_detail"
            _sql = (
                """SELECT
                        compare_type 
                    FROM
                        %s
                    WHERE
	                    report_base_id = :report_base_id
                    GROUP BY
                        compare_type"""
                % table_name
            )
            all_compare_types = db.session.execute(
                _sql, {"report_base_id": report_base_id}
            )
            page_data = db.to_dict(all_compare_types.fetchall())
        return self._success_response(data=page_data)


class AllCompareResult(ApiView):
    """获取所有比对结果"""

    def get(self, report_base_id):
        key = request.args.get("key")

        with DataBase() as db:
            table_name = ""
            if key == "detail":
                table_name = "all_rpm_report"
            elif key == "compare":
                table_name = "report_detail_base"
            elif key == "different":
                table_name = "abi_differences_compare"
            elif key == "diffservice":
                table_name = "diff_service_detail"
            _sql = (
                """SELECT
                        compare_result 
                    FROM
                        %s
                    WHERE
	                    report_base_id = :report_base_id
                    GROUP BY
                        compare_result"""
                % table_name
            )
            all_compare_types = db.session.execute(
                _sql, {"report_base_id": report_base_id}
            )
            page_data = db.to_dict(all_compare_types.fetchall())
        return self._success_response(data=page_data)


class ReportVersionApi(ApiView):
    """修改/删除报告"""

    def post(self, report_base_id):
        """修改报告标题"""
        version = request.get_json().get("version")
        with DataBase() as db:
            report = (
                db.session.query(ReportBase)
                .filter(ReportBase.id == report_base_id)
                .first()
            )
            report.title = version
            db.session.commit()
        return self._success_response()

    @dberror
    def delete(self, report_base_id):
        "删除单个报告（下方所有数据都将清空）"
        with DataBase() as db:
            try:
                report = (
                    db.session.query(ReportBase)
                    .filter(ReportBase.id == report_base_id)
                    .first()
                )
                report.state = 'deleting'
                db.session.commit()
                db.session.execute(
                    "call clean_error_report(:report_base_id);",
                    {"report_base_id": report_base_id},
                )
                db.session.commit()
            except SQLAlchemyError as error:
                logger.info(f"Delete report failed, report id: {report_base_id}")
                logger.error(error)
                db.session.rollback()
                raise SQLAlchemyError
        return self._success_response(data="报告删除成功")


class MdDetailApi(ApiView):
    """
    md文档详情
    """

    @dberror
    def get(self, report_base_id):
        with DataBase() as db:
            detail_path = request.args.get("detail_path")
            md_detail = (
                db.session.query(MdDetail)
                .filter(
                    MdDetail.report_base_id == report_base_id,
                    MdDetail.detail_path == detail_path,
                )
                .first()
            )
        return self._success_response(data=MdDetail_Schema(many=False).dump(md_detail))

class DiffServiceCSVDetailApi(ApiView):
    """
    diff_service-csv文档详情
    """

    @dberror
    def get(self, page, limit):
        path = request.args.get("path")
        order_by = request.args.get("order_by")
        order_by_mode = request.args.get("order_by_mode", "asc")
        report_base_id =  request.args.get("report_base_id")
        compare_type = request.args.get("compare_type")
        compare_result = request.args.get("compare_result")
        with DataBase() as db:
            filter_compare_report = db.session.query(DiffServiceDetail).filter(
                DiffServiceDetail.report_base_id == report_base_id,
                DiffServiceDetail.detail_path == path
            )
            if compare_type:
                filter_compare_report = filter_compare_report.filter(
                    DiffServiceDetail.compare_type == compare_type
                )
            if compare_result:
                filter_compare_report = filter_compare_report.filter(
                    DiffServiceDetail.compare_result == compare_result
                )
            if all([order_by, order_by_mode]):
                order_by = asc(order_by) if order_by_mode == "asc" else desc(order_by)
                filter_compare_report = filter_compare_report.order_by(order_by)
            total = filter_compare_report.count()
            offset = (page - 1) * limit
            page_data = filter_compare_report.offset(offset).limit(limit).all()
        response_data = {
            "total": total,
            "pages": DiffServiceCSVDetail_Schema(many=True).dump(page_data),
        }
        return self._success_response(data=response_data)
    