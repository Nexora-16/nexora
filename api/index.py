import sys
import os
import traceback

# Force pip-installed packages to take precedence over Vercel's vendored packages
_pip_paths = [p for p in sys.path if 'site-packages' in p or '.venv' in p]
_other_paths = [p for p in sys.path if p not in _pip_paths]
sys.path = _pip_paths + _other_paths

# Add project root so app.py and all its modules can be found
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_import_error = None
_import_tb = None
app = None

try:
    from app import app
except Exception as e:
    _import_error = f"{type(e).__name__}: {e}"
    _import_tb = traceback.format_exc()

    def app(environ, start_response):
        body = f"IMPORT FAILED:\n{_import_error}\n\nTraceback:\n{_import_tb}".encode()
        start_response("500 Internal Server Error", [
            ("Content-Type", "text/plain"),
            ("Content-Length", str(len(body))),
        ])
        return [body]
