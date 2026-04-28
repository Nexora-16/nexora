from config_db import db
from datetime import datetime, date


class Gasto(db.Model):
    __tablename__ = "gasto"
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, nullable=False)
    concepto   = db.Column(db.String(100), nullable=False)
    monto      = db.Column(db.Float, nullable=False)
    categoria  = db.Column(db.String(50), nullable=False, default="Otros")
    fecha      = db.Column(db.Date, nullable=False, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
