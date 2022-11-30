import os
import shutil
import hashlib
from application import app
from application.core.storage import AnalysisReport
from libs.exceptions import DatabaseException
from libs.log import logger
from libs.conf import settings
from libs.command import cmd
from .worker import make_celery
from celery.exceptions import Ignore

# celery -A application.core.task.tasks:celery worker

celery = make_celery(app)


@celery.task(bind=True)
def storage_report_task(self, file):
    """
    持久化存储导入tar.gz报告
    """
    analysis_report = AnalysisReport(task=self)
    try:
        meta = {"total": 0, "finish": 0, "setep": "import", "task_type": "tar-gz"}
        self.update_state(
            state="PROGRESS",
            meta=meta,
        )
        analysis_report.storage(file=file)
    except DatabaseException:
        logger.error(f"rpm报告基础信息插入失败: {file}")
        os.remove(file)
        self.update_state(
            state="FAILED",
            meta={
                "message": "rpm报告基础信息插入失败",
            },
        )
        raise Ignore()


def run_oecp(source_iso, target_iso):
    oecp_workdir = os.path.join(settings.workspace, "iso-work")
    if not os.path.exists(oecp_workdir):
        os.makedirs(oecp_workdir)
    iso = source_iso + target_iso
    iso_path_hash = hashlib.md5(iso.encode("UTF-8")).hexdigest()
    unpack_folder = os.path.join(settings.workspace, "unpack-tmp-report", iso_path_hash)
    if os.path.exists(unpack_folder):
        shutil.rmtree(unpack_folder)
    os.makedirs(unpack_folder, exist_ok=True)
    shell_cmd = f"python3 {settings.cli} {source_iso} {target_iso} -w {oecp_workdir} -o {unpack_folder}"
    code, _, error = cmd(shell_cmd)
    _file = None
    if code:
        logger.error(error)
        return False, _file

    for file in os.listdir(unpack_folder):
        _file = os.path.join(unpack_folder, file)
        if os.path.isdir(_file):
            break

    return False if code else True, _file


@celery.task(bind=True)
def storage_iso_task(self, source_iso, target_iso):
    """
    通过分析ISO生成差异化报告,并执行持久化存储
    """
    meta = {"total": 0, "finish": 0, "setep": "oecp", "task_type": "iso"}
    self.update_state(
        state="PROGRESS",
        meta=meta,
    )
    oecp_analysis_result, file = run_oecp(source_iso=source_iso, target_iso=target_iso)
    if not oecp_analysis_result:
        logger.error("调用OECP差异化分析工具比对发生错误")
        meta.update(dict(message="OECP差异化分析工具比对发生错误"))
        self.update_state(
            state="FAILED",
            meta=meta,
        )
        raise Ignore()
    analysis_report = AnalysisReport(task=self)
    try:
        meta["setep"] = "import"
        self.update_state(
            state="PROGRESS",
            meta=meta,
        )
        analysis_report.storage(clean=False, iso=True, report=file)
    except DatabaseException:
        logger.error(f"ISO分析比对持久化错误")
        raise Ignore()


@celery.task(bind=True)
def merge_file_task(self, target_filename, task, total_chunks):
    """
    合并文件上传的文件分片
    """
    chunk = 1
    total_chunks = int(total_chunks)
    self.update_state(
        state="PROGRESS",
        meta=dict(total=total_chunks, finish=0),
    )
    meta = None
    try:
        with open(
            os.path.join(settings.workspace, "iso-storage", target_filename),
            "wb",
        ) as target_file:
            while chunk <= total_chunks:
                try:
                    _filename = task + str(chunk)
                    tmp_file = os.path.join(
                        settings.workspace,
                        "iso-storage",
                        "tmp",
                        target_filename,
                        _filename,
                    )
                    if not os.path.exists(tmp_file):
                        meta = dict(
                            total=total_chunks,
                            finish=chunk,
                            message=f"分片文件不存在: {tmp_file}",
                        )

                        logger.warning(f"分片文件不存在: {tmp_file}")
                        raise Ignore()
                    source_file = open(tmp_file, "rb")
                    target_file.write(source_file.read())
                    source_file.close()
                except IOError as error:
                    logger.error(f"分片文件合并错误,文件：{tmp_file} 错误信息： {error}")
                    meta = dict(
                        total=total_chunks,
                        finish=chunk,
                        message=f"分片文件合并错误,文件：{tmp_file}",
                    )

                    raise Ignore()
                else:
                    self.update_state(
                        state="PROGRESS",
                        meta=dict(total=total_chunks, finish=chunk),
                    )
                    chunk += 1
                finally:
                    os.remove(tmp_file)
    except (Ignore, IOError, FileNotFoundError) as error:
        logger.error(error)
        if os.path.exists(
            os.path.join(settings.workspace, "iso-storage", target_filename)
        ):
            os.remove(os.path.join(settings.workspace, "iso-storage", target_filename))
        shutil.rmtree(
            os.path.join(
                settings.workspace,
                "iso-storage",
                "tmp",
                target_filename,
            )
        )
        if not meta:
            meta = dict(message="镜像合并出错")
        self.update_state(state="FAILED", meta=meta)
        raise Ignore()
