from flask import Blueprint, request, jsonify, g
from models.client import Client
from models.pedido import Pedido
from config_db import db
from utils.auth_utils import require_auth

clients_bp = Blueprint("clients", __name__)

TIPOS_VALIDOS = {"Restaurante", "Cafetería", "Panadería", "Escuela", "Hotel", "Particular", "Otro"}


@clients_bp.route("/clientes", methods=["GET"])
@require_auth
def listar_clientes():
    clientes = Client.query.filter_by(user_id=g.user_id).order_by(Client.nombre).all()
    result = []
    for c in clientes:
        pedidos = Pedido.query.filter_by(client_id=c.id, user_id=g.user_id).all()
        total_gastado = sum(p.precio * p.cantidad for p in pedidos)
        result.append({
            "id":            c.id,
            "nombre":        c.nombre,
            "tipo":          c.tipo,
            "telefono":      c.telefono or "",
            "notas":         c.notas or "",
            "total_pedidos": len(pedidos),
            "total_gastado": round(total_gastado, 2)
        })
    return jsonify(result)


@clients_bp.route("/clientes", methods=["POST"])
@require_auth
def agregar_cliente():
    data     = request.get_json(silent=True) or {}
    nombre   = (data.get("nombre") or "").strip()
    tipo     = (data.get("tipo") or "Particular").strip()
    telefono = (data.get("telefono") or "").strip() or None
    notas    = (data.get("notas") or "").strip() or None

    if not nombre:
        return jsonify({"msg": "El nombre del cliente es requerido"}), 400
    if tipo not in TIPOS_VALIDOS:
        return jsonify({"msg": f"Tipo inválido"}), 400

    c = Client(user_id=g.user_id, nombre=nombre, tipo=tipo, telefono=telefono, notas=notas)
    db.session.add(c)
    db.session.commit()
    return jsonify({"msg": "Cliente agregado", "id": c.id}), 201


@clients_bp.route("/clientes/<int:client_id>", methods=["PUT"])
@require_auth
def editar_cliente(client_id):
    c = Client.query.filter_by(id=client_id, user_id=g.user_id).first()
    if not c:
        return jsonify({"msg": "Cliente no encontrado"}), 404

    data     = request.get_json(silent=True) or {}
    nombre   = (data.get("nombre") or "").strip()
    tipo     = (data.get("tipo") or "Particular").strip()
    telefono = (data.get("telefono") or "").strip() or None
    notas    = (data.get("notas") or "").strip() or None

    if not nombre:
        return jsonify({"msg": "El nombre del cliente es requerido"}), 400

    c.nombre   = nombre
    c.tipo     = tipo
    c.telefono = telefono
    c.notas    = notas
    db.session.commit()
    return jsonify({"msg": "Cliente actualizado"})


@clients_bp.route("/clientes/<int:client_id>", methods=["DELETE"])
@require_auth
def eliminar_cliente(client_id):
    c = Client.query.filter_by(id=client_id, user_id=g.user_id).first()
    if not c:
        return jsonify({"msg": "Cliente no encontrado"}), 404
    db.session.delete(c)
    db.session.commit()
    return jsonify({"msg": "Cliente eliminado"})


@clients_bp.route("/clientes/<int:client_id>/pedidos", methods=["GET"])
@require_auth
def pedidos_cliente(client_id):
    c = Client.query.filter_by(id=client_id, user_id=g.user_id).first()
    if not c:
        return jsonify({"msg": "Cliente no encontrado"}), 404
    pedidos = Pedido.query.filter_by(client_id=client_id, user_id=g.user_id).order_by(Pedido.created_at.desc()).all()
    return jsonify([{
        "id":             p.id,
        "product_nombre": p.product_nombre,
        "cantidad":       p.cantidad,
        "precio":         p.precio,
        "ganancia":       round((p.precio - p.costo) * p.cantidad, 2),
        "created_at":     p.created_at.strftime("%d/%m/%Y %H:%M")
    } for p in pedidos])
