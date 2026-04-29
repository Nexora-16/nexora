from datetime import date, datetime
from flask import Blueprint, request, jsonify, g
from config_db import db
from models.sucursal import Sucursal
from models.sale import Sale
from models.gasto import Gasto
from models.product import Product
from models.usuario import Usuario
from utils.auth_utils import require_auth, require_admin

sucursales_bp = Blueprint("sucursales", __name__)


@sucursales_bp.route("/sucursales", methods=["GET"])
@require_auth
@require_admin
def listar_sucursales():
    sucursales = Sucursal.query.filter_by(owner_id=g.user_id).all()
    result = []
    for s in sucursales:
        empleados = Usuario.query.filter_by(owner_id=g.user_id, sucursal_id=s.id).count()
        result.append({
            "id":        s.id,
            "nombre":    s.nombre,
            "direccion": s.direccion or "",
            "empleados": empleados,
        })
    return jsonify(result)


@sucursales_bp.route("/sucursales", methods=["POST"])
@require_auth
@require_admin
def crear_sucursal():
    data      = request.get_json(silent=True) or {}
    nombre    = (data.get("nombre") or "").strip()
    direccion = (data.get("direccion") or "").strip() or None

    if not nombre:
        return jsonify({"msg": "El nombre de la sucursal es requerido"}), 400

    suc = Sucursal(owner_id=g.user_id, nombre=nombre, direccion=direccion)
    db.session.add(suc)
    db.session.commit()
    return jsonify({"msg": "Sucursal creada", "id": suc.id}), 201


@sucursales_bp.route("/sucursales/<int:suc_id>", methods=["PUT"])
@require_auth
@require_admin
def editar_sucursal(suc_id):
    suc = Sucursal.query.filter_by(id=suc_id, owner_id=g.user_id).first()
    if not suc:
        return jsonify({"msg": "Sucursal no encontrada"}), 404

    data = request.get_json(silent=True) or {}
    nombre    = (data.get("nombre") or "").strip()
    direccion = (data.get("direccion") or "").strip() or None

    if not nombre:
        return jsonify({"msg": "El nombre de la sucursal es requerido"}), 400

    suc.nombre    = nombre
    suc.direccion = direccion
    db.session.commit()
    return jsonify({"msg": "Sucursal actualizada"})


@sucursales_bp.route("/sucursales/<int:suc_id>", methods=["DELETE"])
@require_auth
@require_admin
def eliminar_sucursal(suc_id):
    suc = Sucursal.query.filter_by(id=suc_id, owner_id=g.user_id).first()
    if not suc:
        return jsonify({"msg": "Sucursal no encontrada"}), 404
    # remove assigned employees' branch
    Usuario.query.filter_by(owner_id=g.user_id, sucursal_id=suc_id).update({"sucursal_id": None})
    db.session.delete(suc)
    db.session.commit()
    return jsonify({"msg": "Sucursal eliminada"})


@sucursales_bp.route("/sucursales/<int:suc_id>/stats", methods=["GET"])
@require_auth
@require_admin
def stats_sucursal(suc_id):
    suc = Sucursal.query.filter_by(id=suc_id, owner_id=g.user_id).first()
    if not suc:
        return jsonify({"msg": "Sucursal no encontrada"}), 404

    hoy = date.today()

    ventas_hoy = Sale.query.filter_by(user_id=g.user_id, sucursal_id=suc_id).filter(
        db.func.date(Sale.created_at) == hoy
    ).all()

    ingresos_hoy  = sum(v.precio * v.cantidad for v in ventas_hoy)
    ganancia_hoy  = sum((v.precio - v.costo) * v.cantidad for v in ventas_hoy)

    gastos_hoy = Gasto.query.filter_by(user_id=g.user_id, sucursal_id=suc_id).filter(
        Gasto.fecha == hoy
    ).all()
    total_gastos_hoy = sum(g_obj.monto for g_obj in gastos_hoy)

    productos = Product.query.filter_by(user_id=g.user_id, sucursal_id=suc_id).all()
    stock_bajo = [p.nombre for p in productos if p.stock is not None and p.stock <= 5]

    return jsonify({
        "nombre":           suc.nombre,
        "ventas_hoy":       len(ventas_hoy),
        "ingresos_hoy":     round(ingresos_hoy, 2),
        "ganancia_hoy":     round(ganancia_hoy, 2),
        "gastos_hoy":       round(total_gastos_hoy, 2),
        "productos_total":  len(productos),
        "stock_bajo":       stock_bajo,
    })
