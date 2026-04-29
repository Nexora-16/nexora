from flask import Blueprint, request, jsonify, g
from services.business_service import analizar_negocio
from services.storage_service import agregar_producto
from models.product import Product
from config_db import db
from utils.auth_utils import require_auth, require_admin, scoped_query, scoped_attrs

business_bp = Blueprint("business", __name__)


@business_bp.route("/business", methods=["POST"])
@require_auth
@require_admin
def business():
    data = request.get_json(silent=True) or {}

    producto = (data.get("producto") or "").strip()
    stock = data.get("stock")
    costo = data.get("costo")
    venta = data.get("venta")

    if not producto:
        return jsonify({"msg": "El nombre del producto es requerido"}), 400
    if stock is None or not isinstance(stock, int) or stock < 0:
        return jsonify({"msg": "El stock debe ser un número entero no negativo"}), 400
    if costo is None or float(costo) < 0:
        return jsonify({"msg": "El costo debe ser un número no negativo"}), 400
    if venta is None or float(venta) < 0:
        return jsonify({"msg": "El precio de venta debe ser un número no negativo"}), 400

    costo = float(costo)
    venta = float(venta)

    attrs = scoped_attrs()
    agregar_producto({"producto": producto, "stock": stock, "costo": costo, "venta": venta, **attrs})
    respuesta = analizar_negocio(producto, stock, costo, venta, g.owner_id)

    return jsonify({"respuesta": respuesta})


@business_bp.route("/productos", methods=["GET"])
@require_auth
def obtener_productos():
    productos = scoped_query(Product).all()
    return jsonify([
        {"id": p.id, "producto": p.nombre, "stock": p.stock, "costo": p.costo, "venta": p.venta}
        for p in productos
    ])


@business_bp.route("/productos/<int:product_id>", methods=["PUT"])
@require_auth
@require_admin
def editar_producto(product_id):
    p = Product.query.filter_by(id=product_id, user_id=g.owner_id).first()
    if not p:
        return jsonify({"msg": "Producto no encontrado"}), 404

    data = request.get_json(silent=True) or {}
    nombre = (data.get("producto") or "").strip()
    stock  = data.get("stock")
    costo  = data.get("costo")
    venta  = data.get("venta")

    if not nombre:
        return jsonify({"msg": "El nombre del producto es requerido"}), 400
    if stock is None or not isinstance(stock, int) or stock < 0:
        return jsonify({"msg": "El stock debe ser un número entero no negativo"}), 400
    if costo is None or float(costo) < 0:
        return jsonify({"msg": "El costo debe ser un número no negativo"}), 400
    if venta is None or float(venta) < 0:
        return jsonify({"msg": "El precio de venta debe ser un número no negativo"}), 400

    p.nombre = nombre
    p.stock  = stock
    p.costo  = float(costo)
    p.venta  = float(venta)
    db.session.commit()

    return jsonify({"msg": "Producto actualizado"})


@business_bp.route("/productos/<int:product_id>", methods=["DELETE"])
@require_auth
@require_admin
def eliminar_producto(product_id):
    p = Product.query.filter_by(id=product_id, user_id=g.owner_id).first()
    if not p:
        return jsonify({"msg": "Producto no encontrado"}), 404

    db.session.delete(p)
    db.session.commit()

    return jsonify({"msg": "Producto eliminado"})
