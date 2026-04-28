from models.resource import Resource
from config_db import db

def guardar_recurso(data):
    recurso = Resource.query.filter_by(user_id=data["user_id"]).first()

    if recurso:
        recurso.alquiler = data["alquiler"]
        recurso.empleados = data["empleados"]
        recurso.ubicacion = data["ubicacion"]
    else:
        recurso = Resource(
            alquiler=data["alquiler"],
            empleados=data["empleados"],
            ubicacion=data["ubicacion"],
            user_id=data["user_id"]
        )
        db.session.add(recurso)

    db.session.commit()


def obtener_recurso(user_id):
    recurso = Resource.query.filter_by(user_id=user_id).first()

    if not recurso:
        return None

    return {
        "alquiler": recurso.alquiler,
        "empleados": recurso.empleados,
        "ubicacion": recurso.ubicacion
    }