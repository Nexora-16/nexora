import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_import_error = None
app = None

try:
    from app import app
except Exception as e:
    _import_error = f"{type(e).__name__}: {e}\n\n{traceback.format_exc()}"

    def app(environ, start_response):
        body = f"Boot error: {_import_error}".encode()
        start_response("500 Internal Server Error", [
            ("Content-Type", "text/plain"),
            ("Content-Length", str(len(body))),
        ])
        return [body]
