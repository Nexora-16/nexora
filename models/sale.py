from config_db import db
from datetime import datetime


class Sale(db.Model):
    __tablename__ = "sale"
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    nombre     = db.Column(db.String(100), nullable=False)
    cantidad   = db.Column(db.Integer, nullable=False)
    precio     = db.Column(db.Float, nullable=False)
    costo      = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
