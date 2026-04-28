from flask import Blueprint, request, jsonify, g
from models.recipe_item import RecipeItem
from models.product import Product
from models.insumo import Insumo
from config_db import db
from utils.auth_utils import require_auth

recipes_bp = Blueprint("recipes", __name__)


def _calcular_costo_receta(product_id, user_id):
    items = RecipeItem.query.filter_by(product_id=product_id).all()
    total = 0.0
    for item in items:
        ins = Insumo.query.filter_by(id=item.insumo_id, user_id=user_id).first()
        if ins:
            total += ins.costo_unitario * item.cantidad
    return round(total, 4)


@recipes_bp.route("/productos/<int:product_id>/receta", methods=["GET"])
@require_auth
def obtener_receta(product_id):
    p = Product.query.filter_by(id=product_id, user_id=g.user_id).first()
    if not p:
        return jsonify({"msg": "Producto no encontrado"}), 404

    items = RecipeItem.query.filter_by(product_id=product_id).all()
    result = []
    for item in items:
        ins = Insumo.query.filter_by(id=item.insumo_id, user_id=g.user_id).first()
        if ins:
            result.append({
                "id":           item.id,
                "insumo_id":    ins.id,
                "insumo_nombre": ins.nombre,
                "unidad":       ins.unidad,
                "cantidad":     item.cantidad,
                "insumo_stock": ins.stock
            })
    return jsonify(result)


@recipes_bp.route("/productos/<int:product_id>/receta", methods=["POST"])
@require_auth
def guardar_receta(product_id):
    p = Product.query.filter_by(id=product_id, user_id=g.user_id).first()
    if not p:
        return jsonify({"msg": "Producto no encontrado"}), 404

    items_data = request.get_json(silent=True)
    if not isinstance(items_data, list):
        return jsonify({"msg": "Se esperaba una lista de ingredientes"}), 400

    for item in items_data:
        if not isinstance(item.get("cantidad"), (int, float)) or item["cantidad"] <= 0:
            return jsonify({"msg": "Cada ingrediente debe tener cantidad mayor a 0"}), 400
        ins = Insumo.query.filter_by(id=item.get("insumo_id"), user_id=g.user_id).first()
        if not ins:
            return jsonify({"msg": f"Insumo {item.get('insumo_id')} no encontrado"}), 404

    RecipeItem.query.filter_by(product_id=product_id).delete()
    for item in items_data:
        db.session.add(RecipeItem(
            product_id=product_id,
            insumo_id=int(item["insumo_id"]),
            cantidad=float(item["cantidad"])
        ))

    p.costo = _calcular_costo_receta(product_id, g.user_id)
    db.session.commit()
    return jsonify({"msg": "Receta guardada", "costo_calculado": p.costo})
