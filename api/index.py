import sys
import os
import repr as _repr

db_url = os.environ.get("DATABASE_URL", "NOT_SET")

lines = [
    f"DATABASE_URL length: {len(db_url)}",
    f"DATABASE_URL repr: {repr(db_url[:80])}",
    f"First chars hex: {db_url[:10].encode().hex()}",
]


def app(environ, start_response):
    body = "\n".join(lines).encode()
    start_response("200 OK", [("Content-Type", "text/plain"), ("Content-Length", str(len(body)))])
    return [body]
