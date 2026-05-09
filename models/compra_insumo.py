from config_db import db
from datetime import datetime


class CompraInsumo(db.Model):
    __tablename__ = "compra_insumo"
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, nullable=False)
    sucursal_id    = db.Column(db.Integer, nullable=True)
    insumo_id      = db.Column(db.Integer, nullable=False)
    insumo_nombre  = db.Column(db.String(100), nullable=False)
    cantidad       = db.Column(db.Float, nullable=False)
    unidad         = db.Column(db.String(20), nullable=True)
    costo_total    = db.Column(db.Float, nullable=True)
    estado         = db.Column(db.String(20), nullable=False, default="llegado")
    fecha_esperada = db.Column(db.DateTime, nullable=True)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
