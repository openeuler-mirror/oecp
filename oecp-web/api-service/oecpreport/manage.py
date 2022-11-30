#!/usr/bin/python3
import os


try:
    if not os.getenv("SETTINGS_FILE", None):
        os.environ["SETTINGS_FILE"] = "/etc/oecpreport/conf.ini"

    from libs.conf import settings
except RuntimeError as error:
    raise Exception(error)

from application import init_app
from flask_cors import CORS

app = init_app()
CORS(app, resources=r"/*")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
