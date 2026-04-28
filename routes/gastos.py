from flask import Blueprint, request, jsonify, g
from models.gasto import Gasto
from config_db import db
from utils.auth_utils import require_auth
from datetime import date

gastos_bp = Blueprint("gastos", __name__)

CATEGORIAS = {"Gas", "Electricidad", "Packaging", "Insumos", "Sueldos", "Otros"}


@gastos_bp.route("/gastos", methods=["GET"])
@require_auth
def listar_gastos():
    gastos = Gasto.query.filter_by(user_id=g.user_id).order_by(Gasto.fecha.desc(), Gasto.created_at.desc()).all()
    return jsonify([{
        "id":        g_.id,
        "concepto":  g_.concepto,
        "monto":     g_.monto,
        "categoria": g_.categoria,
        "fecha":     g_.fecha.strftime("%d/%m/%Y")
    } for g_ in gastos])


@gastos_bp.route("/gastos", methods=["POST"])
@require_auth
def agregar_gasto():
    data      = request.get_json(silent=True) or {}
    concepto  = (data.get("concepto") or "").strip()
    monto     = data.get("monto")
    categoria = (data.get("categoria") or "Otros").strip()
    fecha_str = (data.get("fecha") or "").strip()

    if not concepto:
        return jsonify({"msg": "El concepto es requerido"}), 400
    if monto is None or float(monto) <= 0:
        return jsonify({"msg": "El monto debe ser mayor a 0"}), 400
    if categoria not in CATEGORIAS:
        categoria = "Otros"

    if fecha_str:
        try:
            partes = fecha_str.split("-")
            fecha = date(int(partes[0]), int(partes[1]), int(partes[2]))
        except Exception:
            fecha = date.today()
    else:
        fecha = date.today()

    gasto = Gasto(user_id=g.user_id, concepto=concepto, monto=float(monto),
                  categoria=categoria, fecha=fecha)
    db.session.add(gasto)
    db.session.commit()
    return jsonify({"msg": "Gasto registrado", "id": gasto.id}), 201


@gastos_bp.route("/gastos/<int:gasto_id>", methods=["DELETE"])
@require_auth
def eliminar_gasto(gasto_id):
    g_ = Gasto.query.filter_by(id=gasto_id, user_id=g.user_id).first()
    if not g_:
        return jsonify({"msg": "Gasto no encontrado"}), 404
    db.session.delete(g_)
    db.session.commit()
    return jsonify({"msg": "Gasto eliminado"})
