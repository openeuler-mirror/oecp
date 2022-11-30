#!/usr/bin/python3
import sys
from .xmlmap import xml


_codes = ("SUCCESS", "FAIL", "PARAM_ERROR", "ERROR", "SYSTEM_ERROR")


class RspMsg:
    """
    响应的消息内容
    """

    def __init__(self, label="success", **kwargs):
        self._label = label
        self.response_body = {
            "message": kwargs.get("message"),
            "tip": kwargs.get("tip") or True,
        }

    def _code(self, label):
        """
        code对应的状态码
        """
        response_body = xml.content(label)
        response_body["error_code"] = label
        return response_body

    @property
    def response(self):
        """
        获取相应的内容
        """
        body = self._code(self._label)
        self._body(body)
        return self.response_body

    def _body(self, body, zh=True):
        if "message" not in self.response_body or self.response_body["message"] is None:
            self.response_body["message"] = (
                body["message_zh"] if zh else body["message_en"]
            )
        self.response_body["code"] = body["status_code"]

    def body(self, label, zh=True, **kwargs):
        """
        获取响应的信息
        """
        self.response_body["message"] = None
        self.response_body["tip"] = kwargs.get("tip", False) or True
        self.response_body.update(**kwargs)
        if "data" not in kwargs:
            self.response_body["data"] = None
        self._body(self._code(label), zh)
        return self.response_body


def _init():
    module = sys.modules[__name__]
    for code in _codes:
        setattr(module, code, code)
        setattr(module, code.lower(), code)


_init()
respmsg = RspMsg()
__all__ = ["respmsg"]
