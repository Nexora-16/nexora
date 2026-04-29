from flask import Blueprint, request, jsonify, g
from models.recipe_item import RecipeItem
from models.product import Product
from models.insumo import Insumo
from config_db import db
from utils.auth_utils import require_auth, require_admin

recipes_bp = Blueprint("recipes", __name__)


def _calcular_costo_receta(product_id, owner_id):
    """Cost per unit (stored quantities are already per-unit)."""
    items = RecipeItem.query.filter_by(product_id=product_id).all()
    total = 0.0
    for item in items:
        ins = Insumo.query.filter_by(id=item.insumo_id, user_id=owner_id).first()
        if ins:
            total += ins.costo_unitario * item.cantidad
    return round(total, 4)


@recipes_bp.route("/productos/<int:product_id>/receta", methods=["GET"])
@require_auth
def obtener_receta(product_id):
    p = Product.query.filter_by(id=product_id, user_id=g.owner_id).first()
    if not p:
        return jsonify({"msg": "Producto no encontrado"}), 404

    rendimiento = p.rendimiento or 1.0
    items = RecipeItem.query.filter_by(product_id=product_id).all()
    ingredientes = []
    for item in items:
        ins = Insumo.query.filter_by(id=item.insumo_id, user_id=g.owner_id).first()
        if ins:
            ingredientes.append({
                "id":            item.id,
                "insumo_id":     ins.id,
                "insumo_nombre": ins.nombre,
                "unidad":        ins.unidad,
                "cantidad_lote": round(item.cantidad * rendimiento, 6),  # batch qty for display
                "insumo_stock":  ins.stock,
            })

    return jsonify({"rendimiento": rendimiento, "ingredientes": ingredientes})


@recipes_bp.route("/productos/<int:product_id>/receta", methods=["POST"])
@require_auth
@require_admin
def guardar_receta(product_id):
    p = Product.query.filter_by(id=product_id, user_id=g.owner_id).first()
    if not p:
        return jsonify({"msg": "Producto no encontrado"}), 404

    data        = request.get_json(silent=True) or {}
    rendimiento = data.get("rendimiento")
    ingredientes = data.get("ingredientes")

    if not isinstance(ingredientes, list):
        return jsonify({"msg": "Se esperaba una lista de ingredientes"}), 400
    if rendimiento is None or float(rendimiento) <= 0:
        return jsonify({"msg": "El rendimiento debe ser mayor a 0"}), 400

    rendimiento = float(rendimiento)

    for item in ingredientes:
        if not isinstance(item.get("cantidad"), (int, float)) or item["cantidad"] <= 0:
            return jsonify({"msg": "Cada ingrediente debe tener cantidad mayor a 0"}), 400
        ins = Insumo.query.filter_by(id=item.get("insumo_id"), user_id=g.owner_id).first()
        if not ins:
            return jsonify({"msg": f"Insumo {item.get('insumo_id')} no encontrado"}), 404

    p.rendimiento = rendimiento
    RecipeItem.query.filter_by(product_id=product_id).delete()
    for item in ingredientes:
        # Store per-unit quantity = batch_qty / rendimiento
        db.session.add(RecipeItem(
            product_id=product_id,
            insumo_id=int(item["insumo_id"]),
            cantidad=round(float(item["cantidad"]) / rendimiento, 8),
        ))

    p.costo = _calcular_costo_receta(product_id, g.owner_id)
    db.session.commit()
    return jsonify({
        "msg":             "Receta guardada",
        "costo_calculado": p.costo,
        "rendimiento":     rendimiento,
    })
