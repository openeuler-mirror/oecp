#!/usr/bin/python3
import json
import os
import gzip
import shutil
import tarfile
import time
import csv
import hashlib
from itertools import islice
import xlrd
from pymysql import DatabaseError
from libs.exceptions import DatabaseException
from libs.log import logger
from application.models.report import (
    AbiDifferencesCompare,
    AllRpmReport,
    DiffServiceDetail,
    Kernel,
    MdDetail,
    OsvTechnicalReport,
    ReportDetailBase,
    ReportBase,
    RpmRequiresAnaylse,
    RpmfileAnalyse,
)
from libs.sql import DataBase
from libs.conf import settings
from celery.exceptions import Ignore


def tar_gz(gz_file, unpack_file):
    """
    Description: Unzip the compressed package in GZIP format

    """
    try:
        with open(unpack_file, "wb") as file, gzip.GzipFile(gz_file) as gzip_file:
            for data in iter(lambda: gzip_file.read(100 * 1024), b""):
                file.write(data)
    except gzip.BadGzipFile as error:
        logger.error(f"Not a gzipped file: {gz_file},error detail: {error}")


def unpack_tar(tar_file, unpack_folder):
    try:
        _tar_file = tarfile.open(tar_file)
        _tar_file.extractall(unpack_folder)
    except tarfile.ReadError as error:
        raise IOError("The file '%s'  is not a proper tar file ." % tar_file) from error
    finally:
        _tar_file.close()


# truncate table all_rpm_report;
# truncate table interface_change;
# truncate table osv_technical_report;
# truncate table report_base;
# truncate table report_change_info;
# truncate table report_detail_base;
# truncate table abi_differences_compare;
# TRUNCATE table rpmfile_analyse;
# TRUNCATE table kernel;
# TRUNCATE table md_detail;
# TRUNCATE table diff_service_detail;
# TRUNCATE table rpm_requires_analyse;


class AnalysisReport:
    """
    分析差异化报告
    """

    def __init__(self, task, report_path=None) -> None:
        self.task = task
        self.report_path = report_path
        self._report_base_id = 0
        self.db = None
        self._async_error = None

    def _load_csv(self, csv_file, index=1, end=None):
        if not os.path.exists(csv_file):
            return []
        try:
            with open(csv_file) as file:
                csv_reader = csv.reader(file)
                return [row for row in islice(csv_reader, index, end)]
        except IOError as error:
            logger.warning(f"Load csv failed: {error}")
            return []

    def _unpack_tar_gz(self, gz_file):
        """
        解压缩tar.gz文件
        """
        wait_unpack_file = os.path.join(self.report_path, "waiting-unpack.tar")
        tar_gz(gz_file, unpack_file=wait_unpack_file)
        unpack_tar(tar_file=wait_unpack_file, unpack_folder=self.report_path)
        if os.path.exists(wait_unpack_file):
            os.remove(wait_unpack_file)
        files = os.listdir(self.report_path)
        if len(files) == 1:
            self.report_path = os.path.join(self.report_path, files[-1])

    def _insert_db(self, datas, model):
        with DataBase() as db:
            try:
                db.batch_add(datas, model)
                db.session.commit()
            except Exception as err:
                logger.error(err)
                db.session.rollback()
                raise DatabaseException(err)

    @property
    def rpm_report_header(self):
        file = os.path.join(self.report_path, "all-rpm-report.csv")
        try:
            header = self._load_csv(file, 0, 1)[0]
            return header[0], header[2]
        except IndexError:
            logger.warning(f"The file format is incorrect: {file}")
            self._async_error = "all-rpm-report.csv不是正确的文件格式"
            raise ValueError("all-rpm-report.csv不是正确的文件格式")

    @staticmethod
    def _cut_or_vt(contents: list, length):
        if len(contents) > length:
            return contents[:length]
        elif len(contents) < length:
            return contents.extend([None for _ in range(0, length - len(contents))])
        else:
            return contents

    def _import_all_rpm_report(self, file="all-rpm-report.csv"):
        if not os.path.exists(os.path.join(self.report_path, file)):
            self._async_error = "all-rpm-report.csv文件不存在"
            raise FileNotFoundError("all-rpm-report.csv文件不存在")
        all_rpm_report = self._load_csv(
            csv_file=os.path.join(self.report_path, file), index=2
        )
        fields = (
            "source_binary_rpm_package",
            "source_src_package",
            "compare_binary_rpm_package",
            "compare_src_package",
            "compare_result",
            "compare_detail",
            "compare_type",
            "category_level",
            "same",
            "more",
            "less",
            "diff",
            "report_base_id",
        )
        # 遍历插入数据库中
        wait_insert_all_rpms = list()
        for row in all_rpm_report:
            row = self._cut_or_vt(row, len(fields) - 1)
            row.append(self._report_base_id)
            wait_insert_all_rpms.append(dict(zip(fields, row)))
        self._insert_db(wait_insert_all_rpms, AllRpmReport)

    def _set_rpm_abi(self, compare_detail, detail_path):
        rpm_abi_list = []
        for row in compare_detail:
            new_rpm_abi = row[:-2]
            new_rpm_abi.extend([None, row[-1], detail_path, self._report_base_id])
            rpm_abi_list.append(new_rpm_abi)
        return rpm_abi_list

    def _set_drive_kabi(self, compare_detail, detail_path):
        drive_kabi_list = []
        for row in compare_detail:
            new_drive_kabi = self._cut_or_vt(row, 6) + [
                detail_path,
                row[-1],
                None,
                self._report_base_id,
            ]

            drive_kabi_list.append(new_drive_kabi)
        return drive_kabi_list

    def _set_rpm_requires_analyse(self, detail_path, compare_detail):
        wait_insert_rpm_requires_analyse = list()
        fields = (
            "rpm_package",
            "source_symbol_name",
            "source_package",
            "source_dependence_type",
            "compare_symbol_name",
            "compare_package",
            "compare_dependence_type",
            "compare_result",
            "compare_type",
            "category_level",
            "detail_path",
            "report_base_id",
        )
        for rpm_require in compare_detail:
            rpm_require = self._cut_or_vt(rpm_require, len(fields) - 2)
            rpm_require.extend([detail_path, self._report_base_id])
            wait_insert_rpm_requires_analyse.append(dict(zip(fields, rpm_require)))

        self._insert_db(wait_insert_rpm_requires_analyse, RpmRequiresAnaylse)

    def _set_rpm_files(self, compare_detail, detail_path, compare_type):
        rpm_files_list = []
        if compare_type == "rpm requires":
            self._set_rpm_requires_analyse(detail_path, compare_detail)
            return None

        exists_detail_path = (
            "rpm abi",
            "rpm header",
            "rpm config",
            "rpm service",
            "rpm jabi",
        )
        for row in compare_detail:
            new_rpm_file = self._cut_or_vt(row, 6)
            md_detail_path = row[-1] if compare_type in exists_detail_path else None
            new_rpm_file.extend(
                [detail_path, None, md_detail_path, self._report_base_id]
            )
            rpm_files_list.append(new_rpm_file)
        return rpm_files_list

    def _import_report_detail(self):
        """通过分析all-rpm-report中的数据,读取特定的文件,组合数据"""
        with DataBase() as db:
            all_rpm_report = (
                db.session.query(AllRpmReport)
                .filter(AllRpmReport.report_base_id == self._report_base_id)
                .all()
            )
        fields = (
            "rpm_package",
            "source",
            "compare",
            "compare_result",
            "compare_type",
            "category_level",
            "detail_path",
            "effect_drivers",
            "md_detail_path",
            "report_base_id",
        )
        meta = {"total": 0, "finish": 0, "setep": "import", "message": ""}

        for index, rpm_report in enumerate(all_rpm_report, 1):
            meta["total"] = len(all_rpm_report)
            meta["finish"] = index
            self.task.update_state(
                state="PROGRESS",
                meta=meta,
            )
            if not rpm_report.compare_detail:
                continue
            compare_detail = self._load_csv(
                os.path.join(self.report_path, rpm_report.compare_detail.strip())
            )
            rows = []
            if not compare_detail:
                logger.warning(
                    f"The file does not have the correct content: {rpm_report.compare_detail.strip()}"
                )
                continue
            if rpm_report.compare_type == "drive kabi":
                rows = self._set_drive_kabi(
                    compare_detail, rpm_report.compare_detail.strip()
                )
            else:
                rows = self._set_rpm_files(
                    compare_detail,
                    rpm_report.compare_detail.strip(),
                    rpm_report.compare_type,
                )
            if rows:
                wait_inserts = [dict(zip(fields, row)) for row in rows]
                self._insert_db(wait_inserts, ReportDetailBase)

    def _create_report(self):
        source_version, target_version = self.rpm_report_header
        source_version = source_version.split()[0]
        target_version = target_version.split()[0]
        with DataBase() as db:
            title = target_version.split('-')[0]
            if title:
                count = db.session.query(ReportBase).filter(ReportBase.title == title).count()
                if count > 0:
                    title += "_" + str(count)
            else:
                title = target_version
            report_base = ReportBase(
                title=title,
                source_version=source_version,
                target_version=target_version,
                state="importing",
                create_time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),
            )
            base_report = (
                db.session.query(ReportBase)
                .filter(
                    ReportBase.source_version == source_version,
                    ReportBase.target_version == target_version,
                    ReportBase.state == "importing",
                )
                .first()
            )
            if base_report:
                self._async_error = "存在相同的报告数据"
                raise DatabaseException(message="存在相同的报告数据")
            report_base = db.add(report_base)
            db.session.commit()
            return report_base.id

    def _import_osv(self, file="osv_data_summary.xlsx"):
        osv_analysis = OSVAnalysis(file=os.path.join(self.report_path, file))
        self._insert_db(
            [osv_analysis.osv_data(report_base_id=self._report_base_id)],
            OsvTechnicalReport,
        )

    def _import_abi_diff_compare(self, file="all-differences-report.csv"):
        if not os.path.exists(os.path.join(self.report_path, file)):
            self._async_error = "all-differences-report.csv文件不存在"
            raise FileNotFoundError("all-differences-report.csv文件不存在")
        abi_diff_compare = self._load_csv(csv_file=os.path.join(self.report_path, file))
        fields = (
            "rpm_package",
            "source",
            "compare",
            "compare_result",
            "compare_type",
            "category_level",
            "effect_drivers",
            "detail_path",
            "report_base_id",
        )
        wait_insert_abi_diff_compare = list()
        for row in abi_diff_compare:
            row = self._cut_or_vt(row, len(fields) - 1)
            row.append(self._report_base_id)
            wait_insert_abi_diff_compare.append(dict(zip(fields, row)))
        self._insert_db(wait_insert_abi_diff_compare, AbiDifferencesCompare)

    def _import_report_change_info(self):
        with DataBase() as db:
            db.session.execute(
                "call compare_report_change_info(:report_base_id);",
                {"report_base_id": self._report_base_id},
            )
            db.session.commit()

    def _kabi(self, file):
        sheet = Excel().read_excel_sheet(file=file, sheet_index="kernel")
        fields = (
            "kernel_analyse",
            "more",
            "less",
            "same",
            "diff",
            "report_base_id",
        )
        wait_insert_kabi = list()
        for row in range(1, sheet.nrows):
            row_val = self._cut_or_vt(sheet.row_values(row), len(fields) - 1)
            row_val.append(self._report_base_id)
            wait_insert_kabi.append(dict(zip(fields, row_val)))
        self._insert_db(wait_insert_kabi, Kernel)

    def _rpmabi(self, file):
        sheet = Excel().read_excel_sheet(file=file, sheet_index="rpmabi")
        fields = (
            "rpm_type",
            "rpm_level",
            "package_change",
            "file_less",
            "file_content_change",
            "file_more",
            "file_consistent",
            "report_base_id",
        )
        wait_insert_rpmabi = list()

        all_rpmfile = (
            ["rpm-abi", "ALL"]
            + self._cut_or_vt(sheet.row_values(1)[1:], 4)
            + ["0", self._report_base_id]
        )
        l1_rpmfile = (
            ["rpm-abi", "L1"]
            + self._cut_or_vt(sheet.row_values(2)[1:], 4)
            + ["0", self._report_base_id]
        )
        l2_rpmfile = (
            ["rpm-abi", "L2"]
            + self._cut_or_vt(sheet.row_values(3)[1:], 4)
            + ["0", self._report_base_id]
        )
        for values in (all_rpmfile, l1_rpmfile, l2_rpmfile):
            wait_insert_rpmabi.append(dict(zip(fields, values)))
        self._insert_db(wait_insert_rpmabi, RpmfileAnalyse)

    def __set_rpmfile_analyes_insert_val(
        self, sheet, row, rpm_type, wait_insert_rpmfile_analyes
    ):
        fields = (
            "rpm_type",
            "rpm_level",
            "package_change",
            "file_more",
            "file_less",
            "file_consistent",
            "file_content_change",
            "report_base_id",
        )
        all_rpmfile = (
            [rpm_type, "ALL"]
            + self._cut_or_vt(sheet.row_values(row + 1)[1:], 5)
            + [self._report_base_id]
        )
        l1_rpmfile = (
            [rpm_type, "L1"]
            + self._cut_or_vt(sheet.row_values(row + 2)[1:], 5)
            + [self._report_base_id]
        )
        l2_rpmfile = (
            [rpm_type, "L2"]
            + self._cut_or_vt(sheet.row_values(row + 3)[1:], 5)
            + [self._report_base_id]
        )
        for values in (all_rpmfile, l1_rpmfile, l2_rpmfile):
            wait_insert_rpmfile_analyes.append(dict(zip(fields, values)))

    def _rpmfile_analyes(self, file):
        sheet = Excel().read_excel_sheet(file=file, sheet_index="rpmfile_analyse")
        wait_insert_rpmfile_analyes = list()
        for row in range(0, sheet.nrows):
            rpm_type = sheet.row_values(row)[0]
            if "rpm-service" in rpm_type:
                rpm_type = "rpm-service"
            elif "rpm-config" in rpm_type:
                rpm_type = "rpm-config"
            elif "rpm-cmd" in rpm_type:
                rpm_type = "rpm-cmd"
            elif "rpm-header" in rpm_type:
                rpm_type = "rpm-header"
            elif "rpm-file" in rpm_type:
                rpm_type = "rpm-file"
            elif "rpm-lib" in rpm_type:
                rpm_type = "rpm-lib"
            # elif "rpm-abi" in rpm_type:
            #     rpm_type = "rpm-abi"
            else:
                continue
            self.__set_rpmfile_analyes_insert_val(
                sheet, row, rpm_type, wait_insert_rpmfile_analyes
            )
        self._insert_db(wait_insert_rpmfile_analyes, RpmfileAnalyse)

    def _import_rpmfile_kabi(self, file_name="single_calculate.xlsx"):
        file = os.path.join(self.report_path, file_name)
        if not os.path.exists(file):
            self._async_error = "single_calculate.xlsx文件不存在"
            raise FileNotFoundError("single_calculate.xlsx文件不存在")
        self._kabi(file)
        self._rpmabi(file)
        self._rpmfile_analyes(file)

    def _diff_service_detail(self, detail_path):
        diff_service_detail = self._load_csv(
            os.path.join(self.report_path, detail_path.strip())
        )
        fields = (
            "rpm_package",
            "source",
            "compare",
            "compare_result",
            "compare_type",
            "file_name",
            "detail_path",
            "report_base_id",
        )
        wait_insert_diff_service = []

        for diff_service in diff_service_detail:
            diff_service = self._cut_or_vt(diff_service, len(fields) - 2)
            diff_service.extend([detail_path, self._report_base_id])
            wait_insert_diff_service.append(dict(zip(fields, diff_service)))
        self._insert_db(wait_insert_diff_service, DiffServiceDetail)

    def _read_md(self, md_detail_path):
        try:
            md_content = None
            with open(
                os.path.join(self.report_path, md_detail_path),
                "r",
                encoding="utf-8",
            ) as file:
                md_content = file.read()
        except (IOError, FileNotFoundError) as error:
            logger.warning(
                f"Insert md detail error, detail path: {md_detail_path} error: {error}."
            )
        return md_content

    def _from_abi_diff_import_md(self):
        with DataBase() as db:
            all_differences_report = (
                db.session.query(AbiDifferencesCompare)
                .filter(
                    AbiDifferencesCompare.report_base_id == self._report_base_id,
                    AbiDifferencesCompare.detail_path != "",
                )
                .all()
            )
        wait_insert_md_details = list()
        for differences_report in all_differences_report:
            if differences_report.compare_type == "rpm service":
                self._diff_service_detail(differences_report.detail_path)
                continue
            wait_insert_md_details.append(
                dict(
                    report_base_id=self._report_base_id,
                    detail_path=differences_report.detail_path,
                    md_content=self._read_md(differences_report.detail_path),
                )
            )
        self._insert_db(wait_insert_md_details, MdDetail)

    def _from_report_detail_import_md(self):
        with DataBase() as db:
            report_details = (
                db.session.query(ReportDetailBase)
                .filter(
                    ReportDetailBase.report_base_id == self._report_base_id,
                    ReportDetailBase.md_detail_path != "",
                )
                .all()
            )
        wait_insert_md_details = list()
        for report_detail in report_details:
            wait_insert_md_details.append(
                dict(
                    report_base_id=self._report_base_id,
                    detail_path=report_detail.md_detail_path,
                    md_content=self._read_md(report_detail.md_detail_path),
                )
            )
        self._insert_db(wait_insert_md_details, MdDetail)

    def _import_md_detail(self):
        self._from_abi_diff_import_md()
        self._from_report_detail_import_md()

    def storage(self, file=None, clean=True, iso=False, report=None):
        if report:
            self.report_path = report
        else:
            self.report_path = os.path.join(
                settings.workspace,
                "unpack-tmp-report",
                hashlib.md5(file.encode("UTF-8")).hexdigest(),
            )
            if clean and os.path.exists(self.report_path):
                shutil.rmtree(self.report_path)
            os.makedirs(self.report_path, exist_ok=True)

        if not iso:
            self._unpack_tar_gz(gz_file=file)
        try:
            self._report_base_id = self._create_report()
            if self._report_base_id == 0:
                self._async_error = "基础报告信息导入错误"
                raise DatabaseException(message="基础报告信息导入错误")
            self._import_all_rpm_report()
            self._import_osv()
            self._import_report_detail()
            self._import_abi_diff_compare()
            self._import_md_detail()
            self._import_report_change_info()
            self._import_rpmfile_kabi()
        except (DatabaseError, DatabaseException, ValueError, Exception) as err:
            with DataBase() as db:
                db.session.execute(
                    "call clean_error_report(:report_base_id);",
                    {"report_base_id": self._report_base_id},
                )
                db.session.commit()
            logger.error(err)
            if not iso and file:
                os.remove(file)
            if not self._async_error:
                self._async_error = "持久化发生错误,请稍后重试"
            self.task.update_state(
                state="FAILED",
                meta={
                    "message": self._async_error,
                },
            )
            raise Ignore(self._async_error)


class Excel:
    """
    excel表格读取,内容获取
    """

    def read_excel_sheet(self, file, sheet_index=0):
        osv_summary = xlrd.open_workbook(file)
        if isinstance(sheet_index, int):
            osv_summary_sheet = osv_summary.sheet_by_index(sheet_index)
        else:
            osv_summary_sheet = osv_summary.sheet_by_name(sheet_index)
        return osv_summary_sheet


class OSVAnalysis:
    """
    OSV报告结果解析
    """

    def __init__(self, file) -> None:
        self.osv_file = file

    def _analysis_test_item(self, sheet, start_row=8, end_row=None):
        if end_row is None:
            end_row = sheet.nrows
        osv_test_item_data = list()
        test_fields = ("test_item", "describe", "test_result", "conclusion")
        while start_row < end_row:
            dimension_result = dict(dimension=None, test_items=[])
            row_value = sheet.row_values(start_row)
            if row_value[1]:
                dimension_result["dimension"] = row_value[1]
            dimension_result["test_items"].append(
                dict(zip(test_fields, row_value[2:5] + row_value[6:7]))
            )
            while True:
                try:
                    if sheet.row_values(start_row + 1)[1]:
                        start_row = start_row + 1
                        break
                except IndexError:
                    start_row = start_row + 1
                    break
                start_row = start_row + 1
                row_value = sheet.row_values(start_row)
                dimension_result["test_items"].append(
                    dict(zip(test_fields, row_value[2:5] + row_value[6:7]))
                )
            osv_test_item_data.append(dimension_result)

        return osv_test_item_data

    def osv_data(self, report_base_id):
        sheet = Excel().read_excel_sheet(file=self.osv_file)
        osv_technical_report = dict(report_base_id=report_base_id)
        try:
            osv_technical_report["osv_version"] = sheet.row_values(1)[5]
            osv_technical_report["architecture"] = sheet.row_values(2)[5]
            osv_technical_report["release_addr"] = sheet.row_values(3)[5]
            osv_technical_report["checksum"] = sheet.row_values(4)[5]
            osv_technical_report["base_home_old_ver"] = sheet.row_values(5)[5]
            osv_technical_report["detection_result"] = sheet.row_values(2)[1]
            osv_technical_report["detail_json"] = json.dumps(
                self._analysis_test_item(sheet=sheet)
            )
        except IndexError as error:
            logger.error(error)
            raise ValueError("osv_data_summary.xlsx文件格式有误")

        return osv_technical_report
