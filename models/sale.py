from config_db import db
from datetime import datetime


class Sale(db.Model):
    __tablename__ = "sale"
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, nullable=False)
    product_id  = db.Column(db.Integer, nullable=True)
    nombre      = db.Column(db.String(100), nullable=False)
    cantidad    = db.Column(db.Float, nullable=False)
    precio      = db.Column(db.Float, nullable=False)
    costo       = db.Column(db.Float, nullable=False)
    unidad      = db.Column(db.String(20), nullable=True)
    sucursal_id = db.Column(db.Integer, nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
