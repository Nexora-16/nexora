import sys
import os

# Reorder sys.path to try pip packages first
_pip = [p for p in sys.path if 'site-packages' in p or '.venv' in p]
_other = [p for p in sys.path if p not in _pip]
sys.path = _pip + _other

import flask_sqlalchemy as _fsql
import sqlalchemy as _sa

lines = [
    f"flask_sqlalchemy: {getattr(_fsql, '__file__', '?')}",
    f"flask_sqlalchemy version: {getattr(_fsql, '__version__', '?')}",
    f"sqlalchemy: {getattr(_sa, '__file__', '?')}",
    f"sqlalchemy version: {getattr(_sa, '__version__', '?')}",
    "",
    "SYS.PATH:",
] + sys.path[:20]


def app(environ, start_response):
    body = "\n".join(lines).encode()
    start_response("200 OK", [("Content-Type", "text/plain"), ("Content-Length", str(len(body)))])
    return [body]
