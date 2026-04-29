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

    if items:
        faltantes = []
        for item in items:
            ins = Insumo.query.filter_by(id=item.insumo_id, user_id=g.owner_id).first()
            if not ins:
                continue
            necesario = item.cantidad * cantidad
            if ins.stock < necesario:
                faltantes.append(f"{ins.nombre}: necesitás {necesario:.3f} {ins.unidad}, tenés {ins.stock:.3f}")
        if faltantes:
            return jsonify({"msg": "Stock de insumos insuficiente:\n" + "\n".join(faltantes)}), 400

        for item in items:
            ins = Insumo.query.filter_by(id=item.insumo_id, user_id=g.owner_id).first()
            if ins:
                ins.stock = round(ins.stock - item.cantidad * cantidad, 6)

        costo = sum(
            (Insumo.query.filter_by(id=item.insumo_id, user_id=g.owner_id).first().costo_unitario or 0) * item.cantidad
            for item in items
            if Insumo.query.filter_by(id=item.insumo_id, user_id=g.owner_id).first()
        )
        p.costo = round(costo, 4)

    p.stock = round((p.stock or 0) + cantidad, 6)
    attrs = scoped_attrs()
    log = ProductionLog(product_id=p.id, nombre=p.nombre, cantidad=cantidad, unidad=p.unidad or "u", **attrs)
    db.session.add(log)
    db.session.commit()

    return jsonify({
        "msg":        "Producción registrada",
        "stock_nuevo": p.stock,
        "unidad":      p.unidad or "u",
        "con_receta":  bool(items),
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
