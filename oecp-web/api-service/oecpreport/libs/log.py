#!/usr/bin/python3
import os
import re
import pathlib
import logging
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
from .conf import settings


__all__ = ["logger", "Log"]
__version__ = "1.0.0"


class Log:
    """
    operation log of the system
    """

    def __init__(
        self, name=__name__, path=None, default_handler=TimedRotatingFileHandler
    ):
        self.__path = (
            path if path else os.path.join(settings.log_path, settings.log_name)
        )

        self._create_log()

        self._file_handler = self._timerotating_filehandler
        if isinstance(logging.FileHandler, type(default_handler)):
            self._file_handler = self._handler

        if isinstance(RotatingFileHandler, type(default_handler)):
            self._file_handler = self._rotating_filehandler

        if not hasattr(self, "_file_handler"):
            raise ValueError(
                "The logging handle is incorrectly set and can only be TimedRotatingFileHandler, FileHandler,RotatingFileHandler"
            )

        self.__logger = logging.getLogger(name)
        self.__logger.setLevel(settings.log_level)
        self.__init_handler()

    def _create_log(self):
        if os.path.exists(self.__path):
            return
        try:
            os.makedirs(os.path.split(self.__path)[0])
        except FileExistsError:
            pathlib.Path(self.__path).touch()

    def __init_handler(self):
        self.__set_handler()
        self.__set_formatter()

    @property
    def _handler(self):
        """文件输出的handler"""
        file_handler = logging.FileHandler(self.__path, encoding="utf-8")
        return file_handler

    @property
    def _timerotating_filehandler(self):
        """日期分割的日志文件"""
        file_handler = TimedRotatingFileHandler(
            self.__path, when="D", interval=1, backupCount=settings.log_backup_count
        )
        file_handler.suffix = "%Y-%m-%d_%H-%M.log"
        file_handler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}.log$")
        return file_handler

    @property
    def _rotating_filehandler(self):
        file_handler = RotatingFileHandler(
            self.__path,
            maxBytes=settings.log_max_bytes,
            backupCount=settings.log_backup_count,
        )
        return file_handler

    def __set_handler(self):
        self._file_handler.setLevel(settings.log_level)
        self.__logger.addHandler(self._file_handler)

    def __set_formatter(self):
        formatter = logging.Formatter(
            settings.log_formatter,
            datefmt="%a, %d %b %Y %H:%M:%S",
        )
        self._file_handler.setFormatter(formatter)

    @property
    def logger(self):
        """
        Gets the logger property
        """
        return self.__logger

    @property
    def file_handler(self):
        """
        The file handle to the log
        """
        return self._file_handler


logger = Log().logger
