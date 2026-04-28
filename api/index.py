import sys
import os

def app(environ, start_response):
    body = f"Python {sys.version} | PATH OK".encode()
    start_response("200 OK", [("Content-Type", "text/plain"), ("Content-Length", str(len(body)))])
    return [body]
