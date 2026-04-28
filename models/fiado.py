from config_db import db
from datetime import datetime


class Fiado(db.Model):
    __tablename__ = "fiado"
    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, nullable=False)
    client_id     = db.Column(db.Integer, nullable=False)
    client_nombre = db.Column(db.String(100), nullable=False)
    concepto      = db.Column(db.String(200), nullable=False)
    monto         = db.Column(db.Float, nullable=False)
    pagado        = db.Column(db.Boolean, nullable=False, default=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    pagado_at     = db.Column(db.DateTime, nullable=True)
