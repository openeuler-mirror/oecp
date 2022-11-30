#!/usr/bin/python3
from flask import Flask
from libs.conf import settings


app = Flask(__name__)
app.config.update(
    CELERY_BROKER_URL=f"redis://{settings.redis}/1",
    CELERY_RESULT_BACKEND=f"redis://{settings.redis}/1",
)


def init_app():
    """
    初始化创建app
    return : 生成的app对象
    """

    from .apps import blueprint

    # 注册蓝图
    for blue, api in blueprint:
        api.init_app(app)
        app.register_blueprint(blue)
    return app
