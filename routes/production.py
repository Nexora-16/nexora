from flask import Blueprint, request, jsonify, g
from models.production_log import ProductionLog
from models.recipe_item import RecipeItem
from models.product import Product
from models.insumo import Insumo
from config_db import db
from utils.auth_utils import require_auth, scoped_query, scoped_attrs

production_bp = Blueprint("production", __name__)


@production_bp.route("/produccion", methods=["POST"])
@require_auth
def registrar_produccion():
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

    items = RecipeItem.query.filter_by(product_id=product_id).all()
    consumo = []

    if items:
        insumo_map = {
            item.insumo_id: Insumo.query.filter_by(id=item.insumo_id, user_id=g.owner_id).first()
            for item in items
        }
        costo = 0.0
        for item in items:
            ins = insumo_map.get(item.insumo_id)
            if not ins:
                continue
            usado = round(item.cantidad * cantidad, 6)
            costo += (ins.costo_unitario or 0) * item.cantidad
            consumo.append({"nombre": ins.nombre, "usado": usado, "unidad": ins.unidad})

        p.costo = round(costo, 4)

    p.stock = round((p.stock or 0) + cantidad, 6)
    attrs = scoped_attrs()
    log = ProductionLog(product_id=p.id, nombre=p.nombre, cantidad=cantidad, unidad=p.unidad or "u", **attrs)
    db.session.add(log)
    db.session.commit()

    return jsonify({
        "msg":             "Producción registrada",
        "stock_nuevo":     p.stock,
        "unidad":          p.unidad or "u",
        "con_receta":      bool(items),
        "costo_calculado": p.costo,
        "consumo":         consumo,
    })


@production_bp.route("/produccion", methods=["GET"])
@require_auth
def obtener_produccion():
    logs = scoped_query(ProductionLog).order_by(ProductionLog.created_at.desc()).all()
    return jsonify([{
        "id":         l.id,
        "nombre":     l.nombre,
        "cantidad":   l.cantidad,
        "unidad":     l.unidad or "u",
        "created_at": l.created_at.strftime("%d/%m/%Y %H:%M")
    } for l in logs])
