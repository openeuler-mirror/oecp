from flask.blueprints import Blueprint
from flask_restful import Api
from . import view


__all__ = ["blue_print", "api", "urls"]
blue_print = Blueprint("statistical", __name__)
api = Api()
urls = [
    # 查询软件包比对统计
    (
        view.AllPackageApi,
        "/detail/all-package/<int:report_base_id>",
    ),
    # rpm 的服务文件、命令、配置文件比对结果
    (
        view.RpmServiceCmdConfigApi,
        "/detail/rpm-service-cmd-conf/<int:report_base_id>",
    ),
    (
        view.KernelAnalyseApi,
        "/detail/kernel-analyse/<int:report_base_id>",
    ),
    (
        view.RpmfileAnalyseApi,
        "/detail/rpmfile-analyse/<int:report_base_id>",
    ),
    # 查询接口文件变化、接口参数变化、结构体变化统计
    (
        view.ABIChangeApi,
        "/detail/api-change/<int:report_base_id>",
    )
]
