from flask import Blueprint, request, jsonify, g
from services.resource_service import guardar_recurso, obtener_recurso
from utils.auth_utils import require_auth

resource_bp = Blueprint("resource", __name__)


@resource_bp.route("/recursos", methods=["POST"])
@require_auth
def guardar():
    data = request.get_json(silent=True) or {}

    alquiler = data.get("alquiler", 0)
    empleados = data.get("empleados", 0)
    ubicacion = (data.get("ubicacion") or "").strip()

    if not isinstance(alquiler, (int, float)) or float(alquiler) < 0:
        return jsonify({"msg": "El alquiler debe ser un número no negativo"}), 400
    if not isinstance(empleados, int) or empleados < 0:
        return jsonify({"msg": "Los empleados deben ser un número entero no negativo"}), 400
    if not ubicacion:
        return jsonify({"msg": "La ubicación es requerida"}), 400

    guardar_recurso({
        "alquiler": float(alquiler),
        "empleados": empleados,
        "ubicacion": ubicacion,
        "user_id": g.user_id,
    })
    return jsonify({"msg": "Recursos guardados correctamente"})


@resource_bp.route("/recursos", methods=["GET"])
@require_auth
def obtener():
    recurso = obtener_recurso(g.user_id)
    return jsonify(recurso if recurso else {})
