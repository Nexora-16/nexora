from datetime import datetime, date, timedelta
from flask import Blueprint, request, jsonify, g
from models.insumo import Insumo
from models.compra_insumo import CompraInsumo
from config_db import db
from utils.auth_utils import require_auth, require_admin, scoped_query, scoped_attrs

insumos_bp = Blueprint("insumos", __name__)

UNIDADES_VALIDAS = {"kg", "g", "l", "ml", "u"}


def _compra_dict(c):
    return {
        "id":             c.id,
        "insumo_id":      c.insumo_id,
        "insumo_nombre":  c.insumo_nombre,
        "cantidad":       c.cantidad,
        "unidad":         c.unidad or "u",
        "costo_total":    c.costo_total,
        "estado":         c.estado,
        "fecha_esperada": c.fecha_esperada.strftime("%Y-%m-%d") if c.fecha_esperada else None,
        "created_at":     c.created_at.strftime("%d/%m/%Y %H:%M") if c.created_at else None,
    }


@insumos_bp.route("/insumos", methods=["GET"])
@require_auth
def listar_insumos():
    insumos = scoped_query(Insumo).order_by(Insumo.nombre).all()
    return jsonify([{
        "id":             i.id,
        "nombre":         i.nombre,
        "stock":          i.stock,
        "unidad":         i.unidad,
        "costo_unitario": i.costo_unitario,
        "dias_restock":   i.dias_restock,
        "qty_restock":    i.qty_restock,
        "ultimo_pedido":  i.ultimo_pedido.isoformat() if i.ultimo_pedido else None,
    } for i in insumos])


@insumos_bp.route("/insumos", methods=["POST"])
@require_auth
@require_admin
def agregar_insumo():
    data   = request.get_json(silent=True) or {}
    nombre = (data.get("nombre") or "").strip()
    stock  = data.get("stock")
    unidad = (data.get("unidad") or "").strip()
    costo  = data.get("costo_unitario")

    if not nombre:
        return jsonify({"msg": "El nombre del insumo es requerido"}), 400
    if stock is None or float(stock) < 0:
        return jsonify({"msg": "El stock debe ser un número no negativo"}), 400
    if unidad not in UNIDADES_VALIDAS:
        return jsonify({"msg": f"Unidad inválida. Usá: {', '.join(UNIDADES_VALIDAS)}"}), 400
    if costo is None or float(costo) < 0:
        return jsonify({"msg": "El costo debe ser un número no negativo"}), 400

    attrs = scoped_attrs()
    insumo = Insumo(nombre=nombre, stock=float(stock), unidad=unidad,
                    costo_unitario=float(costo), **attrs)
    db.session.add(insumo)
    db.session.commit()
    return jsonify({"msg": "Insumo agregado", "id": insumo.id}), 201


@insumos_bp.route("/insumos/<int:insumo_id>", methods=["PUT"])
@require_auth
@require_admin
def editar_insumo(insumo_id):
    ins = Insumo.query.filter_by(id=insumo_id, user_id=g.owner_id).first()
    if not ins:
        return jsonify({"msg": "Insumo no encontrado"}), 404

    data   = request.get_json(silent=True) or {}
    nombre = (data.get("nombre") or "").strip()
    stock  = data.get("stock")
    unidad = (data.get("unidad") or "").strip()
    costo  = data.get("costo_unitario")

    if not nombre:
        return jsonify({"msg": "El nombre del insumo es requerido"}), 400
    if stock is None or float(stock) < 0:
        return jsonify({"msg": "El stock debe ser un número no negativo"}), 400
    if unidad not in UNIDADES_VALIDAS:
        return jsonify({"msg": f"Unidad inválida. Usá: {', '.join(UNIDADES_VALIDAS)}"}), 400
    if costo is None or float(costo) < 0:
        return jsonify({"msg": "El costo debe ser un número no negativo"}), 400

    ins.nombre         = nombre
    ins.stock          = float(stock)
    ins.unidad         = unidad
    ins.costo_unitario = float(costo)

    dias = data.get("dias_restock")
    qty  = data.get("qty_restock")
    ins.dias_restock = int(dias) if dias and int(dias) > 0 else None
    ins.qty_restock  = float(qty) if qty and float(qty) > 0 else None

    db.session.commit()
    return jsonify({"msg": "Insumo actualizado"})


@insumos_bp.route("/insumos/<int:insumo_id>", methods=["DELETE"])
@require_auth
@require_admin
def eliminar_insumo(insumo_id):
    ins = Insumo.query.filter_by(id=insumo_id, user_id=g.owner_id).first()
    if not ins:
        return jsonify({"msg": "Insumo no encontrado"}), 404
    db.session.delete(ins)
    db.session.commit()
    return jsonify({"msg": "Insumo eliminado"})


@insumos_bp.route("/insumos/<int:insumo_id>/compra", methods=["POST"])
@require_auth
def registrar_compra(insumo_id):
    ins = Insumo.query.filter_by(id=insumo_id, user_id=g.owner_id).first()
    if not ins:
        return jsonify({"msg": "Insumo no encontrado"}), 404

    data = request.get_json(silent=True) or {}
    try:
        cantidad = float(data.get("cantidad"))
    except (TypeError, ValueError):
        cantidad = None
    if cantidad is None or cantidad <= 0:
        return jsonify({"msg": "La cantidad debe ser un número positivo"}), 400

    costo_total = None
    raw_costo = data.get("costo_total")
    if raw_costo not in (None, "", 0):
        try:
            costo_total = float(raw_costo)
        except (TypeError, ValueError):
            pass

    # Parse optional delivery date
    fecha_esperada = None
    raw_fecha = data.get("fecha_esperada")
    if raw_fecha:
        try:
            fecha_esperada = datetime.strptime(raw_fecha, "%Y-%m-%d")
        except ValueError:
            pass

    hoy = datetime.utcnow().date()
    es_futuro = fecha_esperada and fecha_esperada.date() > hoy

    if es_futuro:
        estado = "pendiente"
    else:
        estado = "llegado"
        ins.stock = round(ins.stock + cantidad, 6)
        ins.ultimo_pedido = datetime.utcnow()
        if costo_total and costo_total > 0:
            ins.costo_unitario = round(costo_total / cantidad, 6)

    attrs = scoped_attrs()
    compra = CompraInsumo(
        insumo_id=ins.id,
        insumo_nombre=ins.nombre,
        cantidad=cantidad,
        unidad=ins.unidad,
        costo_total=costo_total,
        estado=estado,
        fecha_esperada=fecha_esperada,
        **attrs,
    )
    db.session.add(compra)
    db.session.commit()

    if es_futuro:
        return jsonify({
            "msg":    f"Pedido programado para el {fecha_esperada.strftime('%d/%m/%Y')}: {cantidad} {ins.unidad} de {ins.nombre}",
            "estado": "pendiente",
        })
    return jsonify({
        "msg":            f"Llegada registrada: +{cantidad} {ins.unidad} de {ins.nombre}",
        "stock_nuevo":    ins.stock,
        "costo_unitario": ins.costo_unitario,
        "estado":         "llegado",
    })


@insumos_bp.route("/compras/<int:compra_id>/confirmar", methods=["POST"])
@require_auth
def confirmar_compra(compra_id):
    compra = scoped_query(CompraInsumo).filter_by(id=compra_id).first()
    if not compra:
        return jsonify({"msg": "Pedido no encontrado"}), 404
    if compra.estado == "llegado":
        return jsonify({"msg": "Este pedido ya fue confirmado"}), 400

    ins = Insumo.query.filter_by(id=compra.insumo_id, user_id=g.owner_id).first()
    if not ins:
        return jsonify({"msg": "Insumo no encontrado"}), 404

    ins.stock = round(ins.stock + compra.cantidad, 6)
    ins.ultimo_pedido = datetime.utcnow()
    if compra.costo_total and compra.costo_total > 0:
        ins.costo_unitario = round(compra.costo_total / compra.cantidad, 6)

    compra.estado     = "llegado"
    compra.created_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "msg":         f"✓ Llegada confirmada: +{compra.cantidad} {compra.unidad} de {compra.insumo_nombre}",
        "stock_nuevo": ins.stock,
    })


@insumos_bp.route("/compras", methods=["GET"])
@require_auth
def listar_compras():
    compras = scoped_query(CompraInsumo).order_by(CompraInsumo.fecha_esperada.asc().nulls_last(),
                                                   CompraInsumo.created_at.desc()).limit(200).all()
    return jsonify([_compra_dict(c) for c in compras])


@insumos_bp.route("/consumo", methods=["GET"])
@require_auth
def consumo_insumos():
    from models.production_log import ProductionLog
    from models.recipe_item import RecipeItem

    dias = max(1, int(request.args.get("dias", 30)))
    desde = datetime.utcnow() - timedelta(days=dias)

    logs = scoped_query(ProductionLog).filter(ProductionLog.created_at >= desde).all()
    insumos = scoped_query(Insumo).order_by(Insumo.nombre).all()

    resultado = []
    for ins in insumos:
        total = 0.0
        for log in logs:
            item = RecipeItem.query.filter_by(product_id=log.product_id, insumo_id=ins.id).first()
            if item:
                total += item.cantidad * log.cantidad
        if total == 0:
            continue
        promedio_diario = total / dias
        resultado.append({
            "id":                     ins.id,
            "nombre":                 ins.nombre,
            "unidad":                 ins.unidad,
            "consumo_total":          round(total, 3),
            "promedio_diario":        round(promedio_diario, 3),
            "recomendacion_semanal":  round(promedio_diario * 7, 2),
            "recomendacion_quincenal":round(promedio_diario * 15, 2),
        })

    return jsonify(resultado)
