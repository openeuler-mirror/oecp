#!/usr/bin/python3
import re
import typing
from flask.globals import request
from functools import wraps
from flask_restful import Resource
from flask import jsonify
from marshmallow import Schema, ValidationError, types, EXCLUDE, validate as va
from libs.response import respmsg
from libs import response
from libs.log import logger
from libs.exceptions import Error


def dberror(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Error as e:
            logger.error(e)
            return jsonify(respmsg.body(label=response.FAIL, message=e.args[0]))
        except Exception as e:
            logger.error(e)
            return jsonify(respmsg.body(label=response.FAIL, message=e.args[0]))

    return wrapper


def validate(schema, many=False, partial=None, load=False, unknown=EXCLUDE):
    def _validate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            data = request.get_json()
            if load:
                try:
                    model = schema(many=many, unknown=unknown).load(
                        data, partial=partial
                    )
                    kwargs.update(model=model)
                except ValidationError as error:
                    logger.warning(error)
                    return ApiView.validate_fail(message=error.messages)
            # 对数据的有效性做校验
            result = schema(many=many, partial=partial, unknown=unknown).validate(data)
            if isinstance(result, tuple):
                logger.warning(result[-1])
                return ApiView.validate_fail(message=result[-1])
            kwargs.update(data=result)
            return func(*args, **kwargs)

        return wrapper

    return _validate


class BaseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    def validate(
        self,
        data: typing.Union[
            typing.Mapping[str, typing.Any],
            typing.Iterable[typing.Mapping[str, typing.Any]],
        ],
        *,
        many: typing.Optional[bool] = None,
        partial: typing.Optional[typing.Union[bool, types.StrSequenceOrSet]] = None,
    ) -> typing.Dict[str, typing.List[str]]:
        """Validate `data` against the schema, returning a dictionary of
        validation errors.

        :param data: The data to validate.
        :param many: Whether to validate `data` as a collection. If `None`, the
            value for `self.many` is used.
        :param partial: Whether to ignore missing fields and not require
            any fields declared. Propagates down to ``Nested`` fields as well. If
            its value is an iterable, only missing fields listed in that iterable
            will be ignored. Use dot delimiters to specify nested fields.
        :return: A dictionary of validation errors.

        .. versionadded:: 1.1.0
        """
        try:
            validate_data = self._do_load(
                data, many=many, partial=partial, postprocess=False
            )
        except ValidationError as exc:
            return ValidationError, typing.cast(
                typing.Dict[str, typing.List[str]], exc.messages
            )

        return validate_data


class ApiView(Resource):
    """API的基类"""

    def to_dict(self, rows):
        if not rows:
            return []
        return [dict(zip(row.keys(), row)) for row in rows]

    @property
    def data(self):
        return request.get_json()

    def _list_response(self, data):
        return jsonify(data)

    def _success_response(self, data=None, tip=False):
        return jsonify(respmsg.body(label=response.SUCCESS, data=data, tip=tip))

    def _fail_response(self, data=None, message=None):
        return jsonify(respmsg.body(label=response.FAIL, message=message))

    def _response(self, status_code, data=None, message=None):
        return jsonify(respmsg.body(label=status_code, message=message, data=data))

    @staticmethod
    def validate_fail(message=None):
        return jsonify(respmsg.body(label=response.VALIDATE_FAIL, data=message))


class LengthCn(va.Length):
    """比较字符的长度，介于两者之间或等于某一个固定的长度
    等于：
        LengthCn(equql=5)
    介于两者之间：
        LengthCn(max=10,min=0)
    """

    message_min = "小于最小长度 {min}."
    message_max = "超过最大长度 {max}."
    message_all = "长度必须在 {min} 和 {max}."
    message_equal = "长度必须 {equal}."


class RangeCn(va.Range):
    """比较一个数据是否在这个范围内、
        可以是大于一个数、小于一个数
        同样也存在等于的场景
    min_inclusive=True   包含最小值
    max_inclusive=True   包含最大值

    """

    message_min = "必须是 {min_op} {{min}}."
    message_max = "必须是 {max_op} {{max}}."
    message_all = "必须是 {min_op} {{min}} 和 {max_op} {{max}}."

    message_gte = "大于或等于"
    message_gt = "大于"
    message_lte = "小于或等于"
    message_lt = "小于"


class URLCn(va.URL):
    """url地址的匹配"""

    default_message = "不是一个正常的URL地址"


class EmailCn(va.Email):
    """email地址判断"""

    default_message = "不是一个正常的Email地址"


class EqualCn(va.Equal):
    """值是否相等的判断，可以用于int str bool类型的比较"""

    default_message = "必须等于 {other}"


class DecimalCn(va.Validator):
    """小数的判断，可以指定小数保留的位数"""

    default_message = "不是一个有效的{digit}位小数"

    def __init__(self, digit=1, minus=False, error=None) -> None:
        self.digit = digit
        self.minus = minus
        self.error = error
        self.regex = re.compile("^(\d+|\d+\.\d{1,%s})$" % self.digit)

    def _repr_args(self):
        return "digit={!r},minus={!r}".format(self.digit, self.minus)

    def _format_error(self, message):
        return (self.error or message).format(digit=self.digit)

    def __call__(self, value):
        message = self._format_error(message=self.default_message)

        if not value or not self.regex.match(value):
            raise ValidationError(message)

        return value


def is_idcard_number(id_number):
    """验证是否是身份证号码"""
    if len(id_number) != 18 and len(id_number) != 15:
        print("身份证号码长度错误")
        return False
    regularExpression = (
        "(^[1-9]\\d{5}(18|19|20)\\d{2}((0[1-9])|(10|11|12))(([0-2][1-9])|10|20|30|31)\\d{3}[0-9Xx]$)|"
        "(^[1-9]\\d{5}\\d{2}((0[1-9])|(10|11|12))(([0-2][1-9])|10|20|30|31)\\d{3}$)"
    )
    # 假设18位身份证号码:41000119910101123X  410001 19910101 123X
    # ^开头
    # [1-9] 第一位1-9中的一个      4
    # \\d{5} 五位数字           10001（前六位省市县地区）
    # (18|19|20)                19（现阶段可能取值范围18xx-20xx年）
    # \\d{2}                    91（年份）
    # ((0[1-9])|(10|11|12))     01（月份）
    # (([0-2][1-9])|10|20|30|31)01（日期）
    # \\d{3} 三位数字            123（第十七位奇数代表男，偶数代表女）
    # [0-9Xx] 0123456789Xx其中的一个 X（第十八位为校验值）
    # $结尾

    # 假设15位身份证号码:410001910101123  410001 910101 123
    # ^开头
    # [1-9] 第一位1-9中的一个      4
    # \\d{5} 五位数字           10001（前六位省市县地区）
    # \\d{2}                    91（年份）
    # ((0[1-9])|(10|11|12))     01（月份）
    # (([0-2][1-9])|10|20|30|31)01（日期）
    # \\d{3} 三位数字            123（第十五位奇数代表男，偶数代表女），15位身份证不含X
    # $结尾
    if re.match(regularExpression, id_number):
        if len(id_number) == 18:
            n = id_number.upper()
            # 前十七位加权因子
            var = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
            # 这是除以11后，可能产生的11位余数对应的验证码
            var_id = ["1", "0", "X", "9", "8", "7", "6", "5", "4", "3", "2"]

            sum = 0
            for i in range(0, 17):
                sum += int(n[i]) * var[i]
            sum %= 11
            if (var_id[sum]) != str(n[17]):
                print("身份证号规则核验失败，校验码应为", var_id[sum], "，当前校验码是：", n[17])
                return False
        return True
    else:
        return False
