from flask import Blueprint, request, jsonify, g
from models.sale import Sale
from models.product import Product
from config_db import db
from utils.auth_utils import require_auth, scoped_query, scoped_attrs

sales_bp = Blueprint("sales", __name__)


@sales_bp.route("/ventas", methods=["POST"])
@require_auth
def registrar_venta():
    data       = request.get_json(silent=True) or {}
    product_id = data.get("product_id")
    cantidad   = data.get("cantidad")

    if not product_id:
        return jsonify({"msg": "Producto requerido"}), 400
    if not isinstance(cantidad, int) or cantidad <= 0:
        return jsonify({"msg": "La cantidad debe ser un entero positivo"}), 400

    p = Product.query.filter_by(id=product_id, user_id=g.owner_id).first()
    if not p:
        return jsonify({"msg": "Producto no encontrado"}), 404
    if p.stock < cantidad:
        return jsonify({"msg": f"Stock insuficiente. Disponible: {p.stock}"}), 400

    p.stock -= cantidad
    attrs = scoped_attrs()
    sale = Sale(product_id=p.id, nombre=p.nombre, cantidad=cantidad,
                precio=p.venta, costo=p.costo, **attrs)
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
        "precio":     v.precio,
        "costo":      v.costo,
        "ganancia":   round((v.precio - v.costo) * v.cantidad, 2),
        "created_at": v.created_at.strftime("%d/%m/%Y %H:%M")
    } for v in ventas])
