from config_db import db


class Usuario(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    username    = db.Column(db.String(50), unique=True, nullable=False)
    password    = db.Column(db.String(256), nullable=False)
    role        = db.Column(db.String(20), nullable=False, default="admin")
    owner_id    = db.Column(db.Integer, nullable=True)   # for employees: admin's user_id
    sucursal_id = db.Column(db.Integer, nullable=True)   # for employees: assigned branch
