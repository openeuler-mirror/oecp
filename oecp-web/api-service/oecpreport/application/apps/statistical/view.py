from application.apps.base import ApiView
from application.apps.base import dberror
from application.apps.statistical.serialize import (
    ReportChangeInfo_Schema,
    ReportInterfaceChange_Schema,
    KernelAnalyse_Schema,
    Rpmfile_Analyse_Schema,
)
from libs.sql import DataBase
from application.models.report import InterfaceChange, ReportChangeInfo, RpmfileAnalyse, Kernel


class AllPackageApi(ApiView):
    """
    查询软件包比对统计
    """

    @dberror
    def get(self, report_base_id):
        with DataBase() as db:
            report_change_info = (
                db.session.query(ReportChangeInfo)
                .filter(ReportChangeInfo.report_base_id == report_base_id)
                .order_by(ReportChangeInfo.level)
                .all()
            )
        return self._success_response(
            data=ReportChangeInfo_Schema(many=True).dump(report_change_info)
        )


class RpmServiceCmdConfigApi(ApiView):
    """
    rpm 的服务文件、命令、配置文件比对结果
    """

    @dberror
    def get(self, report_base_id):
        with DataBase() as db:
            _sql = """SELECT
                    s.rpm_level,	s.package_change AS s_package_change,	s.file_more AS s_file_more,	s.file_less AS s_file_less,	s.file_consistent AS s_file_consistent,	s.file_content_change AS s_file_content_change,
                    cmd.package_change AS cmd_package_change,	cmd.file_more AS cmd_file_more,	cmd.file_less AS cmd_file_less,	cmd.file_consistent AS cmd_file_consistent,	cmd.file_content_change AS cmd_file_content_change,
                    c.package_change AS c_package_change,	c.file_more AS c_file_more,	c.file_less AS c_file_less,	c.file_consistent AS c_file_consistent,	c.file_content_change AS c_file_content_change 
                FROM
                    ( SELECT * FROM rpmfile_analyse WHERE report_base_id = :report_base_id AND rpm_type = 'rpm-service' ) s
                    INNER JOIN ( SELECT * FROM rpmfile_analyse WHERE report_base_id = :report_base_id AND rpm_type = 'rpm-cmd' ) cmd ON s.rpm_level = cmd.rpm_level
                    INNER JOIN ( SELECT * FROM rpmfile_analyse WHERE report_base_id = :report_base_id AND rpm_type = 'rpm-config' ) c ON s.rpm_level = c.rpm_level"""
            all_report_data = db.session.execute(_sql, {"report_base_id": report_base_id})
            page_data = db.to_dict(all_report_data.fetchall())
        return self._success_response(data=page_data)

class KernelAnalyseApi(ApiView):
    """核心分析统计数据查询"""
    
    @dberror
    def get(self, report_base_id):
        with DataBase() as db:
            kernel_analyses = (
                db.session.query(Kernel)
                .filter(Kernel.report_base_id == report_base_id)
                .all()
            )
        return self._success_response(
            data=KernelAnalyse_Schema(many=True).dump(kernel_analyses)
        )

class RpmfileAnalyseApi(ApiView):
    """查询文件统计数据"""
    
    @dberror
    def get(self, report_base_id):
        with DataBase() as db:
            data_list = (
                db.session.query(RpmfileAnalyse)
                .filter(RpmfileAnalyse.report_base_id == report_base_id)
                .all()
            )
        return self._success_response(
            data=Rpmfile_Analyse_Schema(many=True).dump(data_list)
        )
    
class ABIChangeApi(ApiView):
    """
    查询接口文件变化、接口参数变化、结构体变化统计
    """

    @dberror
    def get(self, report_base_id):
        with DataBase() as db:
            interface_change = (
                db.session.query(InterfaceChange)
                .filter(InterfaceChange.report_base_id == report_base_id)
                .all()
            )
        return self._success_response(
            data=ReportInterfaceChange_Schema(many=True).dump(interface_change)
        )