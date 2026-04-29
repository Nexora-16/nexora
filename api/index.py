import os

db_url = os.environ.get("DATABASE_URL", "NOT_SET")

lines = [
    f"length: {len(db_url)}",
    f"repr: {repr(db_url[:80])}",
    f"hex: {db_url[:10].encode('utf-8', errors='replace').hex()}",
]


def app(environ, start_response):
    body = "\n".join(lines).encode()
    start_response("200 OK", [("Content-Type", "text/plain"), ("Content-Length", str(len(body)))])
    return [body]
