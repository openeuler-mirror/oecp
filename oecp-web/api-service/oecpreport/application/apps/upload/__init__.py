from flask.blueprints import Blueprint
from flask_restful import Api
from . import view


__all__ = ["blue_print", "api", "urls"]
blue_print = Blueprint("upload", __name__)
api = Api()

urls = [
    # 上传tar.gz的压缩包
    (
        view.ImportReportTarGz,
        "/tar-gz",
    ),
    # 上传大文件ISO
    (
        view.ImportISO,
        "/iso",
    ),
    # 判断上传的文件是否存在
    (
        view.ExistsUploadFile,
        "/exists/upload-file",
    ),
    # 获取后台任务的状态
    (
        view.AsyncTaskStatus,
        "/async/state/<task_id>",
    ),
    # 异步分析iso数据
    (
        view.AnalysisISO,
        "/analysis/iso",
    ),
    # 获取存储的iso文件或删除iso文件
    (
        view.IsoStorage,
        "/storage/iso",
    ),
]
