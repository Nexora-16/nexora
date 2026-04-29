from config_db import db


class Product(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    nombre      = db.Column(db.String(100))
    stock       = db.Column(db.Integer)
    costo       = db.Column(db.Float)
    venta       = db.Column(db.Float)
    user_id     = db.Column(db.Integer)
    sucursal_id = db.Column(db.Integer, nullable=True)
