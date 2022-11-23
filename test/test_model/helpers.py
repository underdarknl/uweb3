import os
from pathlib import Path

from uweb3 import request
from uweb3.libs.sqltalk import mysql, safe_cookie, sqlite


def DatabaseConnection():
    """Returns an SQLTalk database connection to 'uWeb3_model_test'."""
    return mysql.Connect(
        host="localhost", user="stef", passwd="password", db="uweb_test", charset="utf8"
    )


def CookieConnection():
    req = request.Request(
        {
            "REQUEST_METHOD": "GET",
            "host": "localhost",
            "QUERY_STRING": "",
            "REMOTE_ADDR": "127.0.0.1",
            "PATH_INFO": "info",
        },
        None,
        None,
    )
    req.process_request()
    return safe_cookie.Connect(
        req,
        {},
        "secret",
    )


def SqliteConnection():
    path = os.path.join(Path().absolute(), "sqlite.db")
    return sqlite.Connect(path)
