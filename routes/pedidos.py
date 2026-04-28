from flask import Blueprint, request, jsonify, g
from models.pedido import Pedido
from models.client import Client
from models.product import Product
from config_db import db
from utils.auth_utils import require_auth

pedidos_bp = Blueprint("pedidos", __name__)


@pedidos_bp.route("/pedidos", methods=["GET"])
@require_auth
def listar_pedidos():
    pedidos = Pedido.query.filter_by(user_id=g.user_id).order_by(Pedido.created_at.desc()).all()
    return jsonify([{
        "id":             p.id,
        "client_id":      p.client_id,
        "client_nombre":  p.client_nombre,
        "product_nombre": p.product_nombre,
        "cantidad":       p.cantidad,
        "precio":         p.precio,
        "costo":          p.costo,
        "ganancia":       round((p.precio - p.costo) * p.cantidad, 2),
        "created_at":     p.created_at.strftime("%d/%m/%Y %H:%M")
    } for p in pedidos])


@pedidos_bp.route("/pedidos", methods=["POST"])
@require_auth
def registrar_pedido():
    data       = request.get_json(silent=True) or {}
    client_id  = data.get("client_id")
    product_id = data.get("product_id")
    cantidad   = data.get("cantidad")
    precio     = data.get("precio")

    if not client_id:
        return jsonify({"msg": "Cliente requerido"}), 400
    if not product_id:
        return jsonify({"msg": "Producto requerido"}), 400
    if not isinstance(cantidad, int) or cantidad <= 0:
        return jsonify({"msg": "La cantidad debe ser un entero positivo"}), 400
    if precio is None or float(precio) < 0:
        return jsonify({"msg": "El precio debe ser un número no negativo"}), 400

    c = Client.query.filter_by(id=client_id, user_id=g.user_id).first()
    if not c:
        return jsonify({"msg": "Cliente no encontrado"}), 404

    p = Product.query.filter_by(id=product_id, user_id=g.user_id).first()
    if not p:
        return jsonify({"msg": "Producto no encontrado"}), 404
    if p.stock < cantidad:
        return jsonify({"msg": f"Stock insuficiente. Disponible: {p.stock}"}), 400

    p.stock -= cantidad
    pedido = Pedido(
        user_id=g.user_id,
        client_id=c.id,
        client_nombre=c.nombre,
        product_id=p.id,
        product_nombre=p.nombre,
        cantidad=cantidad,
        precio=float(precio),
        costo=p.costo
    )
    db.session.add(pedido)
    db.session.commit()
    return jsonify({"msg": "Pedido registrado", "stock_restante": p.stock})
