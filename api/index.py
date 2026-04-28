import sys

results = []

for pkg in ["flask", "flask_cors", "flask_sqlalchemy", "pg8000", "jwt", "requests"]:
    try:
        __import__(pkg)
        results.append(f"OK: {pkg}")
    except Exception as e:
        results.append(f"FAIL: {pkg} -> {e}")


def app(environ, start_response):
    body = ("\n".join(results)).encode()
    start_response("200 OK", [("Content-Type", "text/plain"), ("Content-Length", str(len(body)))])
    return [body]
