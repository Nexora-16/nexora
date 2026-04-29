from config_db import db
from datetime import datetime


class ProductionLog(db.Model):
    __tablename__ = "production_log"
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, nullable=False)
    product_id  = db.Column(db.Integer, nullable=False)
    nombre      = db.Column(db.String(100), nullable=False)
    cantidad    = db.Column(db.Integer, nullable=False)
    sucursal_id = db.Column(db.Integer, nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
