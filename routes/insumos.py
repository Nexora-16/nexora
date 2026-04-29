from flask import Blueprint, request, jsonify, g
from models.insumo import Insumo
from config_db import db
from utils.auth_utils import require_auth, require_admin, scoped_query, scoped_attrs

insumos_bp = Blueprint("insumos", __name__)

UNIDADES_VALIDAS = {"kg", "g", "l", "ml", "u"}


@insumos_bp.route("/insumos", methods=["GET"])
@require_auth
def listar_insumos():
    insumos = scoped_query(Insumo).order_by(Insumo.nombre).all()
    return jsonify([{
        "id":             i.id,
        "nombre":         i.nombre,
        "stock":          i.stock,
        "unidad":         i.unidad,
        "costo_unitario": i.costo_unitario
    } for i in insumos])


@insumos_bp.route("/insumos", methods=["POST"])
@require_auth
@require_admin
def agregar_insumo():
    data   = request.get_json(silent=True) or {}
    nombre = (data.get("nombre") or "").strip()
    stock  = data.get("stock")
    unidad = (data.get("unidad") or "").strip()
    costo  = data.get("costo_unitario")

    if not nombre:
        return jsonify({"msg": "El nombre del insumo es requerido"}), 400
    if stock is None or float(stock) < 0:
        return jsonify({"msg": "El stock debe ser un número no negativo"}), 400
    if unidad not in UNIDADES_VALIDAS:
        return jsonify({"msg": f"Unidad inválida. Usá: {', '.join(UNIDADES_VALIDAS)}"}), 400
    if costo is None or float(costo) < 0:
        return jsonify({"msg": "El costo debe ser un número no negativo"}), 400

    attrs = scoped_attrs()
    insumo = Insumo(nombre=nombre, stock=float(stock), unidad=unidad,
                    costo_unitario=float(costo), **attrs)
    db.session.add(insumo)
    db.session.commit()
    return jsonify({"msg": "Insumo agregado", "id": insumo.id}), 201


@insumos_bp.route("/insumos/<int:insumo_id>", methods=["PUT"])
@require_auth
@require_admin
def editar_insumo(insumo_id):
    ins = Insumo.query.filter_by(id=insumo_id, user_id=g.owner_id).first()
    if not ins:
        return jsonify({"msg": "Insumo no encontrado"}), 404

    data   = request.get_json(silent=True) or {}
    nombre = (data.get("nombre") or "").strip()
    stock  = data.get("stock")
    unidad = (data.get("unidad") or "").strip()
    costo  = data.get("costo_unitario")

    if not nombre:
        return jsonify({"msg": "El nombre del insumo es requerido"}), 400
    if stock is None or float(stock) < 0:
        return jsonify({"msg": "El stock debe ser un número no negativo"}), 400
    if unidad not in UNIDADES_VALIDAS:
        return jsonify({"msg": f"Unidad inválida. Usá: {', '.join(UNIDADES_VALIDAS)}"}), 400
    if costo is None or float(costo) < 0:
        return jsonify({"msg": "El costo debe ser un número no negativo"}), 400

    ins.nombre         = nombre
    ins.stock          = float(stock)
    ins.unidad         = unidad
    ins.costo_unitario = float(costo)
    db.session.commit()
    return jsonify({"msg": "Insumo actualizado"})


@insumos_bp.route("/insumos/<int:insumo_id>", methods=["DELETE"])
@require_auth
@require_admin
def eliminar_insumo(insumo_id):
    ins = Insumo.query.filter_by(id=insumo_id, user_id=g.owner_id).first()
    if not ins:
        return jsonify({"msg": "Insumo no encontrado"}), 404
    db.session.delete(ins)
    db.session.commit()
    return jsonify({"msg": "Insumo eliminado"})
