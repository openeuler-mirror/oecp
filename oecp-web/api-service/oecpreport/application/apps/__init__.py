#!/usr/bin/python3
from libs.url import include


_url_prefix = "/api/v1"
blueprint = [
    include(("application.apps.upload", _url_prefix + "/upload")),
    include(("application.apps.report", _url_prefix + "/report")),
    include(("application.apps.statistical", _url_prefix + "/statistical")),
]
