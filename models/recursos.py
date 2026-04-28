from config_db import db

class Recursos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    alquiler = db.Column(db.Float)
    empleados = db.Column(db.Integer)
    ubicacion = db.Column(db.String(100))
    user_id = db.Column(db.Integer)