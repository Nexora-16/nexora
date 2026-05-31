import os
import jwt
import datetime
import secrets
import requests as _req
from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash
from config_db import db
from models.usuario import Usuario

exchange_bp = Blueprint("auth_supabase", __name__)

_SUPABASE_URL      = os.environ.get("SUPABASE_URL", "")
_SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")


def _sb_headers():
    return {"apikey": _SUPABASE_ANON_KEY, "Content-Type": "application/json"}


def _get_or_create_user(email):
    user = Usuario.query.filter_by(username=email).first()
    if not user:
        user = Usuario(
            username=email,
            password=generate_password_hash(secrets.token_hex(32)),
            role="admin",
        )
        db.session.add(user)
        db.session.commit()
    return user


def _make_flask_token(user):
    payload = {
        "user_id": user.id,
        "role":    user.role,
        "exp":     datetime.datetime.utcnow() + datetime.timedelta(hours=24),
    }
    if user.role == "empleado":
        payload["owner_id"]    = user.owner_id
        payload["sucursal_id"] = user.sucursal_id
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def _build_response(user, refresh_token):
    result = {"token": _make_flask_token(user), "role": user.role, "refresh_token": refresh_token}
    if user.role == "empleado" and user.sucursal_id:
        from models.sucursal import Sucursal
        suc = Sucursal.query.get(user.sucursal_id)
        result["sucursal_nombre"] = suc.nombre if suc else ""
        result["sucursal_id"]     = user.sucursal_id
    return result


def _translate_sb_error(data):
    msg = (data.get("error_description") or data.get("msg") or data.get("message") or "").lower()
    if "invalid login" in msg or "invalid credentials" in msg or "invalid email or password" in msg:
        return "Email o contraseña incorrectos."
    if "email not confirmed" in msg:
        return "Verificá tu email antes de iniciar sesión."
    if "user already registered" in msg or "already registered" in msg:
        return "Ese email ya está registrado. Iniciá sesión."
    if "password" in msg and any(w in msg for w in ("short", "length", "character", "weak")):
        return "La contraseña debe tener al menos 8 caracteres."
    if "rate" in msg or "too many" in msg:
        return "Demasiados intentos. Esperá unos minutos."
    return msg or "Error de autenticación."


def _not_configured():
    return not _SUPABASE_URL or not _SUPABASE_ANON_KEY


@exchange_bp.route("/auth/login", methods=["POST"])
def auth_login():
    if _not_configured():
        return jsonify({"msg": "Servidor no configurado para Supabase Auth"}), 503
    data     = request.get_json(silent=True) or {}
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return jsonify({"msg": "Email y contraseña requeridos"}), 400
    try:
        resp = _req.post(
            f"{_SUPABASE_URL}/auth/v1/token?grant_type=password",
            headers=_sb_headers(),
            json={"email": email, "password": password},
            timeout=15,
        )
    except Exception:
        return jsonify({"msg": "Error conectando con Supabase"}), 503
    if resp.status_code != 200:
        return jsonify({"msg": _translate_sb_error(resp.json())}), 401
    sb     = resp.json()
    email  = sb.get("user", {}).get("email", email)
    user   = _get_or_create_user(email)
    return jsonify(_build_response(user, sb.get("refresh_token", "")))


@exchange_bp.route("/auth/register", methods=["POST"])
def auth_register():
    if _not_configured():
        return jsonify({"msg": "Servidor no configurado para Supabase Auth"}), 503
    data     = request.get_json(silent=True) or {}
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email:
        return jsonify({"msg": "Email requerido"}), 400
    if len(password) < 8:
        return jsonify({"msg": "La contraseña debe tener al menos 8 caracteres"}), 400
    try:
        resp = _req.post(
            f"{_SUPABASE_URL}/auth/v1/signup",
            headers=_sb_headers(),
            json={"email": email, "password": password},
            timeout=15,
        )
    except Exception:
        return jsonify({"msg": "Error conectando con Supabase"}), 503
    if resp.status_code not in (200, 201):
        return jsonify({"msg": _translate_sb_error(resp.json())}), 400
    return jsonify({"msg": "Cuenta creada. Verificá tu email para activarla."}), 201


@exchange_bp.route("/auth/refresh", methods=["POST"])
def auth_refresh():
    if _not_configured():
        return jsonify({"msg": "Sin configuración Supabase"}), 503
    data          = request.get_json(silent=True) or {}
    refresh_token = (data.get("refresh_token") or "").strip()
    if not refresh_token:
        return jsonify({"msg": "Refresh token requerido"}), 400
    try:
        resp = _req.post(
            f"{_SUPABASE_URL}/auth/v1/token?grant_type=refresh_token",
            headers=_sb_headers(),
            json={"refresh_token": refresh_token},
            timeout=15,
        )
    except Exception:
        return jsonify({"msg": "Error conectando con Supabase"}), 503
    if resp.status_code != 200:
        return jsonify({"msg": "Sesión expirada, iniciá sesión nuevamente"}), 401
    sb    = resp.json()
    email = sb.get("user", {}).get("email", "")
    user  = _get_or_create_user(email)
    return jsonify(_build_response(user, sb.get("refresh_token", "")))


@exchange_bp.route("/auth/logout", methods=["POST"])
def auth_logout():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer ") and _SUPABASE_URL:
        access_token = auth_header.split(" ", 1)[1]
        try:
            _req.post(
                f"{_SUPABASE_URL}/auth/v1/logout",
                headers={**_sb_headers(), "Authorization": f"Bearer {access_token}"},
                timeout=8,
            )
        except Exception:
            pass
    return jsonify({"msg": "Sesión cerrada"})


@exchange_bp.route("/auth/reset", methods=["POST"])
def auth_reset():
    if _not_configured():
        return jsonify({"msg": "Servidor no configurado"}), 503
    data  = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not email:
        return jsonify({"msg": "Email requerido"}), 400
    body = {"email": email}
    redirect_to = data.get("redirect_to", "")
    if redirect_to:
        body["redirect_to"] = redirect_to
    try:
        _req.post(f"{_SUPABASE_URL}/auth/v1/recover", headers=_sb_headers(), json=body, timeout=15)
    except Exception:
        pass
    return jsonify({"msg": "Si el email existe, te enviamos el link de recuperación."})
