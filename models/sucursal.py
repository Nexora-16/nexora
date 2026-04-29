from config_db import db


class Sucursal(db.Model):
    __tablename__ = "sucursal"
    id        = db.Column(db.Integer, primary_key=True)
    owner_id  = db.Column(db.Integer, nullable=False)
    nombre    = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(200), nullable=True)
