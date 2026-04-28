from config_db import db


class RecipeItem(db.Model):
    __tablename__ = "recipe_item"
    id         = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=False)
    insumo_id  = db.Column(db.Integer, nullable=False)
    cantidad   = db.Column(db.Float, nullable=False)
