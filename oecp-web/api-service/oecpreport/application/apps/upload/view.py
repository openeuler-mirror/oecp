from fileinput import filename
import os
import threading
from flask import request, copy_current_request_context
from werkzeug.utils import secure_filename
from application.apps.base import ApiView
from libs.conf import settings
from application.apps.base import dberror
from libs.log import logger
from application.core.task.tasks import (
    storage_iso_task,
    storage_report_task,
    merge_file_task,
)
from application.core.task.tasks import celery


class ImportReportTarGz(ApiView):
    """
    导入tar.gz的报告
    """

    def post(self):
        tar_gz_path = os.path.join(settings.workspace, "report-tar")
        os.makedirs(tar_gz_path, exist_ok=True)
        # 保存文件
        file = request.files["file"]
        if os.path.exists(os.path.join(tar_gz_path, secure_filename(file.filename))):
            return self._fail_response(message="已存在同名的tar.gz文件,请确认内容是否有更新")
        file.save(os.path.join(tar_gz_path, secure_filename(file.filename)))
        task = storage_report_task.delay(
            file=os.path.join(tar_gz_path, secure_filename(file.filename))
        )
        return self._success_response(data=task.id)


class ExistsUploadFile(ApiView):
    """
    待上传的ISO文件是否存在
    """

    def get(self):
        filename = request.args.get("filename")
        iso_storage = os.path.join(settings.workspace, "iso-storage", filename)
        if os.path.exists(iso_storage):
            return self._success_response(data=True)
        return self._success_response(data=False)


class ImportISO(ApiView):
    """
    上传两份不同的iso文件,使用oecp生成差异化报告
    """

    def pass_exit(self):
        pass

    def post(self):
        @copy_current_request_context
        def save(close_exit, iso_folder, file):
            # filepath = os.path.join(iso_folder, secure_filename(file.filename))
            os.makedirs(iso_folder, exist_ok=True)
            task = request.form.get("identifier")
            chunk = request.form.get("chunkNumber", 0)
            if not chunk:
                self._success = False
                logger.warning("The necessary chunking information is missing")
                return
            _filename = task + str(chunk)
            try:
                file.save(os.path.join(iso_folder, _filename))
                close_exit()
            except IOError as error:
                self._success = False
                logger.error(
                    f"Upload ISO error, file info: {_filename} error info: {error} "
                )

        iso_storage = os.path.join(settings.workspace, "iso-storage")
        os.makedirs(iso_storage, exist_ok=True)
        file = request.files["file"]
        filename = request.form.get("filename")
        self._success = True
        normal_exit = file.stream.close
        file.stream.close = self.pass_exit
        thread_task = threading.Thread(
            target=save,
            args=(normal_exit, os.path.join(iso_storage, "tmp", filename), file),
        )
        thread_task.start()
        thread_task.join()
        return self._success_response() if self._success else self._fail_response()

    def get(self):
        """合并ISO分片文件"""
        target_filename = request.args.get("filename")
        task = request.args.get("identifier")
        total_chunks = request.args.get("totalChunks", 0)
        task = merge_file_task.delay(
            target_filename=secure_filename(target_filename),
            task=task,
            total_chunks=total_chunks,
        )
        return self._success_response(data=task.id)


class AnalysisISO(ApiView):
    """
    通过oecp工具分析iso底层变化,生成报告
    """

    @dberror
    def post(self):
        source_iso = self.data.get("source_iso")
        target_iso = self.data.get("target_iso")
        if not all([source_iso, target_iso]):
            return self._fail_response(message="source_iso target_iso为必传项")
        task = storage_iso_task.delay(
            source_iso=os.path.join(settings.workspace, "iso-storage", source_iso),
            target_iso=os.path.join(settings.workspace, "iso-storage", target_iso),
        )
        return self._success_response(data=task.id)


class AsyncTaskStatus(ApiView):
    """
    上传大文件、report数据导入、iso分片文件合并的异步任务结果信息
    """

    def get(self, task_id):
        try:
            async_result = celery.AsyncResult(id=task_id)
            return self._success_response(
                data=dict(result=async_result.result, status=async_result.state)
            )
        except Exception as error:
            logger.error(error)
            return self._fail_response(message="任务信息获取异常")


class IsoStorage(ApiView):
    """
    ISO镜像文件获取或删除
    """

    def get(self):
        _file_path = os.path.join(settings.workspace, "iso-storage")
        files = []
        if os.path.exists(_file_path):
            files = [
                file
                for file in os.listdir(_file_path)
                if os.path.isfile(os.path.join(_file_path, file))
            ]
        return self._success_response(data=files)

    def delete(self):
        file_name = request.args.get("filename", "")
        file = os.path.join(settings.workspace, "iso-storage", file_name)
        if not os.path.exists(file):
            return self._fail_response(message="文件不存在")

        try:
            os.remove(file)
            return self._success_response()
        except IOError as error:
            logger.error(error)
            return self._fail_response(message="文件删除失败")
