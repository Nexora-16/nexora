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
            g.user_id    = payload["user_id"]
            g.role       = payload.get("role", "admin")
            g.owner_id   = payload.get("owner_id", payload["user_id"])
            g.sucursal_id = payload.get("sucursal_id")  # None = all branches (admin)
        except jwt.ExpiredSignatureError:
            return jsonify({"msg": "Sesión expirada, iniciá sesión nuevamente"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"msg": "Token inválido"}), 401

        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if getattr(g, "role", "admin") != "admin":
            return jsonify({"msg": "Acceso solo para administradores"}), 403
        return f(*args, **kwargs)
    return decorated


def scoped_query(model):
    """Base query filtered by owner and (for employees) their branch."""
    q = model.query.filter_by(user_id=g.owner_id)
    if g.sucursal_id is not None:
        q = q.filter_by(sucursal_id=g.sucursal_id)
    return q


def scoped_attrs():
    """Attrs dict for new records scoped to the current user/branch."""
    attrs = {"user_id": g.owner_id}
    if g.sucursal_id is not None:
        attrs["sucursal_id"] = g.sucursal_id
    return attrs
