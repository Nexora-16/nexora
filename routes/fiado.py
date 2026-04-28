from flask import Blueprint, request, jsonify, g
from models.fiado import Fiado
from models.client import Client
from config_db import db
from utils.auth_utils import require_auth
from datetime import datetime

fiado_bp = Blueprint("fiado", __name__)


@fiado_bp.route("/fiado", methods=["GET"])
@require_auth
def listar_fiados():
    fiados = Fiado.query.filter_by(user_id=g.user_id).order_by(Fiado.created_at.desc()).all()
    return jsonify([{
        "id":            f.id,
        "client_id":     f.client_id,
        "client_nombre": f.client_nombre,
        "concepto":      f.concepto,
        "monto":         f.monto,
        "pagado":        f.pagado,
        "created_at":    f.created_at.strftime("%d/%m/%Y %H:%M"),
        "pagado_at":     f.pagado_at.strftime("%d/%m/%Y") if f.pagado_at else None
    } for f in fiados])


@fiado_bp.route("/fiado", methods=["POST"])
@require_auth
def registrar_fiado():
    data      = request.get_json(silent=True) or {}
    client_id = data.get("client_id")
    concepto  = (data.get("concepto") or "").strip()
    monto     = data.get("monto")

    if not client_id:
        return jsonify({"msg": "Cliente requerido"}), 400
    if not concepto:
        return jsonify({"msg": "El concepto es requerido"}), 400
    if monto is None or float(monto) <= 0:
        return jsonify({"msg": "El monto debe ser mayor a 0"}), 400

    c = Client.query.filter_by(id=client_id, user_id=g.user_id).first()
    if not c:
        return jsonify({"msg": "Cliente no encontrado"}), 404

    f = Fiado(user_id=g.user_id, client_id=c.id, client_nombre=c.nombre,
              concepto=concepto, monto=float(monto))
    db.session.add(f)
    db.session.commit()
    return jsonify({"msg": "Deuda registrada", "id": f.id}), 201


@fiado_bp.route("/fiado/<int:fiado_id>/pagar", methods=["PUT"])
@require_auth
def pagar_fiado(fiado_id):
    f = Fiado.query.filter_by(id=fiado_id, user_id=g.user_id).first()
    if not f:
        return jsonify({"msg": "Fiado no encontrado"}), 404
    f.pagado    = True
    f.pagado_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"msg": "Marcado como pagado"})


@fiado_bp.route("/fiado/<int:fiado_id>", methods=["DELETE"])
@require_auth
def eliminar_fiado(fiado_id):
    f = Fiado.query.filter_by(id=fiado_id, user_id=g.user_id).first()
    if not f:
        return jsonify({"msg": "Fiado no encontrado"}), 404
    db.session.delete(f)
    db.session.commit()
    return jsonify({"msg": "Fiado eliminado"})
