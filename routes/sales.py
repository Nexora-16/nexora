from flask import Blueprint, request, jsonify, g
from models.sale import Sale
from models.product import Product
from config_db import db
from utils.auth_utils import require_auth, scoped_query, scoped_attrs
from datetime import datetime, date

sales_bp = Blueprint("sales", __name__)


@sales_bp.route("/ventas", methods=["POST"])
@require_auth
def registrar_venta():
    data       = request.get_json(silent=True) or {}
    product_id = data.get("product_id")
    cantidad   = data.get("cantidad")

    if not product_id:
        return jsonify({"msg": "Producto requerido"}), 400
    try:
        cantidad = float(cantidad)
    except (TypeError, ValueError):
        cantidad = None
    if cantidad is None or cantidad <= 0:
        return jsonify({"msg": "La cantidad debe ser un número positivo"}), 400

    p = Product.query.filter_by(id=product_id, user_id=g.owner_id).first()
    if not p:
        return jsonify({"msg": "Producto no encontrado"}), 404
    if p.stock < cantidad:
        return jsonify({"msg": f"Stock insuficiente. Disponible: {p.stock} {p.unidad or 'u'}"}), 400

    p.stock = round(p.stock - cantidad, 6)
    attrs = scoped_attrs()
    sale = Sale(product_id=p.id, nombre=p.nombre, cantidad=cantidad,
                precio=p.venta, costo=p.costo, unidad=p.unidad or "u", **attrs)
    db.session.add(sale)
    db.session.commit()

    return jsonify({"msg": "Venta registrada", "stock_restante": p.stock})


@sales_bp.route("/ventas", methods=["GET"])
@require_auth
def obtener_ventas():
    ventas = scoped_query(Sale).order_by(Sale.created_at.desc()).all()
    return jsonify([{
        "id":         v.id,
        "nombre":     v.nombre,
        "cantidad":   v.cantidad,
        "unidad":     v.unidad or "u",
        "precio":     v.precio,
        "costo":      v.costo,
        "ganancia":   round((v.precio - v.costo) * v.cantidad, 2),
        "created_at": v.created_at.strftime("%d/%m/%Y %H:%M")
    } for v in ventas])


_METODOS = {"efectivo", "transferencia", "tarjeta"}
_METODO_LABEL = {"efectivo": "Efectivo", "transferencia": "Transferencia", "tarjeta": "Tarjeta"}


@sales_bp.route("/caja", methods=["POST"])
@require_auth
def registrar_venta_caja():
    data   = request.get_json(silent=True) or {}
    metodo = (data.get("metodo_pago") or "efectivo").lower().strip()
    if metodo not in _METODOS:
        metodo = "efectivo"
    try:
        monto = round(float(data.get("monto")), 2)
    except (TypeError, ValueError):
        return jsonify({"msg": "Monto inválido"}), 400
    if monto <= 0:
        return jsonify({"msg": "El monto debe ser mayor a cero"}), 400

    attrs = scoped_attrs()
    sale = Sale(product_id=None, nombre=f"caja:{metodo}",
                cantidad=1, precio=monto, costo=0, unidad="u", **attrs)
    db.session.add(sale)
    db.session.commit()
    return jsonify({"msg": "Venta registrada", "id": sale.id}), 201


@sales_bp.route("/caja/ultima", methods=["DELETE"])
@require_auth
def anular_ultima_venta_caja():
    ultima = (scoped_query(Sale)
              .filter(Sale.nombre.like("caja:%"))
              .order_by(Sale.created_at.desc())
              .first())
    if not ultima:
        return jsonify({"msg": "No hay ventas de caja para anular"}), 404
    db.session.delete(ultima)
    db.session.commit()
    return jsonify({"msg": "Venta anulada"})


@sales_bp.route("/caja/hoy", methods=["GET"])
@require_auth
def ventas_caja_hoy():
    hoy_inicio = datetime.combine(date.today(), datetime.min.time())
    ventas = (scoped_query(Sale)
              .filter(Sale.nombre.like("caja:%"))
              .filter(Sale.created_at >= hoy_inicio)
              .order_by(Sale.created_at.desc())
              .all())
    return jsonify([{
        "id":     v.id,
        "monto":  v.precio,
        "metodo": v.nombre.replace("caja:", ""),
        "label":  _METODO_LABEL.get(v.nombre.replace("caja:", ""), "Efectivo"),
        "hora":   v.created_at.strftime("%H:%M"),
    } for v in ventas])
