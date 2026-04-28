from config_db import db


class Client(db.Model):
    __tablename__ = "client"
    id       = db.Column(db.Integer, primary_key=True)
    user_id  = db.Column(db.Integer, nullable=False)
    nombre   = db.Column(db.String(100), nullable=False)
    tipo     = db.Column(db.String(50), nullable=False, default="Particular")
    telefono = db.Column(db.String(30), nullable=True)
    notas    = db.Column(db.Text, nullable=True)
