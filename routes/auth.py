import jwt
import datetime
from flask import Blueprint, request, jsonify, g, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from config_db import db
from models.usuario import Usuario
from models.sucursal import Sucursal
from utils.auth_utils import require_auth, require_admin

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"msg": "Datos requeridos"}), 400

    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if len(username) < 3:
        return jsonify({"msg": "El usuario debe tener al menos 3 caracteres"}), 400
    if len(password) < 6:
        return jsonify({"msg": "La contraseña debe tener al menos 6 caracteres"}), 400

    if Usuario.query.filter_by(username=username).first():
        return jsonify({"msg": "Ese nombre de usuario ya está en uso"}), 409

    user = Usuario(username=username, password=generate_password_hash(password), role="admin")
    db.session.add(user)
    db.session.commit()

    return jsonify({"msg": "Usuario creado correctamente"}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"msg": "Datos requeridos"}), 400

    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"msg": "Usuario y contraseña requeridos"}), 400

    user = Usuario.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({"msg": "Credenciales incorrectas"}), 401

    payload = {
        "user_id": user.id,
        "role":    user.role,
        "exp":     datetime.datetime.utcnow() + datetime.timedelta(hours=24),
    }
    if user.role == "empleado":
        payload["owner_id"]    = user.owner_id
        payload["sucursal_id"] = user.sucursal_id

    token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

    resp = {"msg": "Login exitoso", "token": token, "role": user.role}
    if user.role == "empleado" and user.sucursal_id:
        suc = Sucursal.query.get(user.sucursal_id)
        resp["sucursal_nombre"] = suc.nombre if suc else ""
        resp["sucursal_id"]     = user.sucursal_id

    return jsonify(resp)


# ── Employee management (admin only) ────────────────────────────────────────

@auth_bp.route("/empleados", methods=["GET"])
@require_auth
@require_admin
def listar_empleados():
    empleados = Usuario.query.filter_by(owner_id=g.user_id, role="empleado").all()
    result = []
    for e in empleados:
        suc = Sucursal.query.get(e.sucursal_id) if e.sucursal_id else None
        result.append({
            "id":              e.id,
            "username":        e.username,
            "sucursal_id":     e.sucursal_id,
            "sucursal_nombre": suc.nombre if suc else "Sin sucursal",
        })
    return jsonify(result)


@auth_bp.route("/empleados", methods=["POST"])
@require_auth
@require_admin
def crear_empleado():
    data        = request.get_json(silent=True) or {}
    username    = (data.get("username") or "").strip()
    password    = data.get("password") or ""
    sucursal_id = data.get("sucursal_id")

    if len(username) < 3:
        return jsonify({"msg": "El usuario debe tener al menos 3 caracteres"}), 400
    if len(password) < 6:
        return jsonify({"msg": "La contraseña debe tener al menos 6 caracteres"}), 400
    if not sucursal_id:
        return jsonify({"msg": "Debe asignar una sucursal al empleado"}), 400

    suc = Sucursal.query.filter_by(id=sucursal_id, owner_id=g.user_id).first()
    if not suc:
        return jsonify({"msg": "Sucursal no encontrada"}), 404

    if Usuario.query.filter_by(username=username).first():
        return jsonify({"msg": "Ese nombre de usuario ya está en uso"}), 409

    emp = Usuario(
        username=username,
        password=generate_password_hash(password),
        role="empleado",
        owner_id=g.user_id,
        sucursal_id=sucursal_id,
    )
    db.session.add(emp)
    db.session.commit()
    return jsonify({"msg": "Empleado creado", "id": emp.id}), 201


@auth_bp.route("/empleados/<int:emp_id>", methods=["DELETE"])
@require_auth
@require_admin
def eliminar_empleado(emp_id):
    emp = Usuario.query.filter_by(id=emp_id, owner_id=g.user_id, role="empleado").first()
    if not emp:
        return jsonify({"msg": "Empleado no encontrado"}), 404
    db.session.delete(emp)
    db.session.commit()
    return jsonify({"msg": "Empleado eliminado"})
