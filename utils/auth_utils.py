import jwt
from functools import wraps
from flask import request, jsonify, g, current_app


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"msg": "Token requerido"}), 401

        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            g.user_id = payload["user_id"]
        except jwt.ExpiredSignatureError:
            return jsonify({"msg": "Sesión expirada, iniciá sesión nuevamente"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"msg": "Token inválido"}), 401

        return f(*args, **kwargs)
    return decorated
