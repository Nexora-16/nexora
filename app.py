import os
import logging
from flask import Flask, send_file, send_from_directory, jsonify
from flask_cors import CORS
from config_db import db
from routes.auth import auth_bp
from routes.business import business_bp
from routes.chat import chat_bp
from routes.resource import resource_bp
from routes.sales import sales_bp
from routes.insumos import insumos_bp
from routes.recipes import recipes_bp
from routes.production import production_bp
from routes.clients import clients_bp
from routes.pedidos import pedidos_bp
from routes.gastos import gastos_bp
from routes.fiado import fiado_bp

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "nexora-dev-secret-key-change-in-production")

_db_url = os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(basedir, "instance", "nexora.db"))
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)
if _db_url.startswith("postgresql://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+pg8000://", 1)
    _db_url = _db_url.split("?")[0]  # strip any ?sslmode= params (pg8000 uses ssl_context)
app.config["SQLALCHEMY_DATABASE_URI"] = _db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
if _db_url.startswith("postgresql+pg8000://"):
    import ssl as _ssl
    _ssl_ctx = _ssl.create_default_context()
    _ssl_ctx.check_hostname = False
    _ssl_ctx.verify_mode = _ssl.CERT_NONE
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"connect_args": {"ssl_context": _ssl_ctx}}
app.config["MEMORIA"] = {}

app.register_blueprint(auth_bp, url_prefix="/api")
app.register_blueprint(business_bp, url_prefix="/api")
app.register_blueprint(chat_bp, url_prefix="/api")
app.register_blueprint(resource_bp, url_prefix="/api")
app.register_blueprint(sales_bp, url_prefix="/api")
app.register_blueprint(insumos_bp, url_prefix="/api")
app.register_blueprint(recipes_bp, url_prefix="/api")
app.register_blueprint(production_bp, url_prefix="/api")
app.register_blueprint(clients_bp, url_prefix="/api")
app.register_blueprint(pedidos_bp, url_prefix="/api")
app.register_blueprint(gastos_bp, url_prefix="/api")
app.register_blueprint(fiado_bp, url_prefix="/api")

db.init_app(app)

_startup_error = None

try:
    with app.app_context():
        from models.product import Product
        from models.resource import Resource
        from models.chat_message import ChatMessage
        from models.sale import Sale
        from models.insumo import Insumo
        from models.recipe_item import RecipeItem
        from models.production_log import ProductionLog
        from models.client import Client
        from models.pedido import Pedido
        from models.gasto import Gasto
        from models.fiado import Fiado

        if _db_url.startswith("sqlite"):
            os.makedirs("instance", exist_ok=True)
        db.create_all()
except Exception as e:
    _startup_error = str(e)
    logging.error(f"Startup DB error: {e}")


@app.route("/health")
def health():
    if _startup_error:
        return jsonify({"status": "error", "detail": _startup_error}), 500
    return jsonify({"status": "ok", "db": _db_url.split("@")[-1] if "@" in _db_url else "sqlite"})


@app.route("/")
def index():
    return send_file("index.html")

@app.route("/manifest.json")
def manifest():
    return send_file("manifest.json")

@app.route("/sw.js")
def service_worker():
    resp = send_file("sw.js", mimetype="application/javascript")
    resp.headers["Service-Worker-Allowed"] = "/"
    return resp

@app.route("/nexora-icon.svg")
def icon():
    return send_file("nexora-icon.svg", mimetype="image/svg+xml")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
