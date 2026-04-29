from config_db import db
from datetime import datetime


class Pedido(db.Model):
    __tablename__ = "pedido"
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, nullable=False)
    client_id      = db.Column(db.Integer, nullable=False)
    client_nombre  = db.Column(db.String(100), nullable=False)
    product_id     = db.Column(db.Integer, nullable=False)
    product_nombre = db.Column(db.String(100), nullable=False)
    cantidad       = db.Column(db.Integer, nullable=False)
    precio         = db.Column(db.Float, nullable=False)
    costo          = db.Column(db.Float, nullable=False)
    sucursal_id    = db.Column(db.Integer, nullable=True)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
