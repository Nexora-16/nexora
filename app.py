import os
import logging
import ssl as _ssl
from flask import Flask, send_file, jsonify
from flask_cors import CORS
from config_db import db

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "nexora-dev-secret-key-change-in-production")

_db_url = os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(basedir, "instance", "nexora.db"))
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)
if _db_url.startswith("postgresql://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+pg8000://", 1)
    _db_url = _db_url.split("?")[0]
app.config["SQLALCHEMY_DATABASE_URI"] = _db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
if _db_url.startswith("postgresql+pg8000://"):
    _ssl_ctx = _ssl.create_default_context()
    _ssl_ctx.check_hostname = False
    _ssl_ctx.verify_mode = _ssl.CERT_NONE
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"connect_args": {"ssl_context": _ssl_ctx}}
app.config["MEMORIA"] = {}

db.init_app(app)

# Import each blueprint separately to isolate failures
_import_errors = {}

def _safe_import(module, attr):
    try:
        import importlib
        mod = importlib.import_module(module)
        return getattr(mod, attr)
    except Exception as e:
        _import_errors[module] = f"{type(e).__name__}: {e}"
        logging.error(f"Import failed {module}: {e}")
        from flask import Blueprint
        return Blueprint(f"dummy_{attr}", __name__)

auth_bp       = _safe_import("routes.auth",       "auth_bp")
business_bp   = _safe_import("routes.business",   "business_bp")
chat_bp       = _safe_import("routes.chat",        "chat_bp")
resource_bp   = _safe_import("routes.resource",   "resource_bp")
sales_bp      = _safe_import("routes.sales",       "sales_bp")
insumos_bp    = _safe_import("routes.insumos",     "insumos_bp")
recipes_bp    = _safe_import("routes.recipes",     "recipes_bp")
production_bp = _safe_import("routes.production",  "production_bp")
clients_bp    = _safe_import("routes.clients",     "clients_bp")
pedidos_bp    = _safe_import("routes.pedidos",     "pedidos_bp")
gastos_bp     = _safe_import("routes.gastos",      "gastos_bp")
fiado_bp      = _safe_import("routes.fiado",       "fiado_bp")

app.register_blueprint(auth_bp,       url_prefix="/api")
app.register_blueprint(business_bp,   url_prefix="/api")
app.register_blueprint(chat_bp,       url_prefix="/api")
app.register_blueprint(resource_bp,   url_prefix="/api")
app.register_blueprint(sales_bp,      url_prefix="/api")
app.register_blueprint(insumos_bp,    url_prefix="/api")
app.register_blueprint(recipes_bp,    url_prefix="/api")
app.register_blueprint(production_bp, url_prefix="/api")
app.register_blueprint(clients_bp,    url_prefix="/api")
app.register_blueprint(pedidos_bp,    url_prefix="/api")
app.register_blueprint(gastos_bp,     url_prefix="/api")
app.register_blueprint(fiado_bp,      url_prefix="/api")

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
    _startup_error = f"{type(e).__name__}: {e}"
    logging.error(f"Startup DB error: {e}")


@app.route("/health")
def health():
    return jsonify({
        "status":        "error" if (_startup_error or _import_errors) else "ok",
        "db":            _db_url.split("@")[-1] if "@" in _db_url else "sqlite",
        "startup_error": _startup_error,
        "import_errors": _import_errors,
    }), (500 if _startup_error else 200)


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
