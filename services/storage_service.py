from models.product import Product
from models.resource import Resource
from config_db import db


def obtener_productos_db(user_id):
    productos = Product.query.filter_by(user_id=user_id).all()
    return [
        {"producto": p.nombre, "stock": p.stock, "costo": p.costo, "venta": p.venta}
        for p in productos
    ]


def agregar_producto(data):
    nuevo = Product(
        nombre=data["producto"],
        stock=data["stock"],
        costo=data["costo"],
        venta=data["venta"],
        user_id=data["user_id"],
    )
    db.session.add(nuevo)
    db.session.commit()


def obtener_recursos_db(user_id):
    r = Resource.query.filter_by(user_id=user_id).first()
    if not r:
        return None
    return {"alquiler": r.alquiler, "empleados": r.empleados, "ubicacion": r.ubicacion}
