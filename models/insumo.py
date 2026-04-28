from config_db import db


class Insumo(db.Model):
    __tablename__ = "insumo"
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, nullable=False)
    nombre         = db.Column(db.String(100), nullable=False)
    stock          = db.Column(db.Float, nullable=False, default=0)
    unidad         = db.Column(db.String(20), nullable=False, default="u")
    costo_unitario = db.Column(db.Float, nullable=False, default=0)
