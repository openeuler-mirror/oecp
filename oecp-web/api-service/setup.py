import os
from distutils.sysconfig import get_python_lib
from setuptools import setup, find_packages


_CONFIG_PATH = "/etc/oecpreport/"
PACKAGE_PATH = get_python_lib()


setup(
    name="oecpreport",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "celery ==5.2.7",
        "Flask ==2.1.3",
        "Flask-RESTful ==0.3.9",
        "Flask-Cors ==3.0.10",
        "marshmallow ==3.17.0",
        "SQLAlchemy ==1.4.39",
        "redis ==4.3.4",
        "PyMySQL ==1.0.2",
        "xlrd ==1.2.0",
    ],
    license="Oecp report",
    author="huanwei.liu",
    data_files=[
        (
            _CONFIG_PATH,
            ["conf.ini"],
        ),
        ("/usr/bin", ["oecp-report"]),
        # ("/lib/systemd/system/", ["oecpreport.service"]),
        (
            os.path.join(PACKAGE_PATH, "oecpreport", "libs", "response"),
            ["oecpreport/libs/response/mapping.xml"],
        ),
    ],
    zip_safe=False,
)
