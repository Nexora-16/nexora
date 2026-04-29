from config_db import db


class Product(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    nombre      = db.Column(db.String(100))
    stock       = db.Column(db.Float)
    costo       = db.Column(db.Float)
    venta       = db.Column(db.Float)
    unidad      = db.Column(db.String(20), nullable=False, default="u")
    user_id     = db.Column(db.Integer)
    sucursal_id = db.Column(db.Integer, nullable=True)
    rendimiento = db.Column(db.Float, nullable=True)
