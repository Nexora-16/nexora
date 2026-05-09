import os
import sys
import logging

from flask import Flask, send_file, jsonify
from flask_cors import CORS
from config_db import db

app = Flask(__name__)
CORS(app)

_boot_errors = []
_import_errors = {}
_startup_error = None

try:
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "nexora-dev-secret-key-change-in-production")

    _db_url = os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(basedir, "instance", "nexora.db"))
    _db_url = _db_url.lstrip('﻿').strip()  # strip BOM and whitespace (PowerShell echo artifact)
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    if _db_url.startswith("postgresql://") and "sslmode" not in _db_url:
        _db_url += "?sslmode=require"
    app.config["SQLALCHEMY_DATABASE_URI"] = _db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    if _db_url.startswith("postgresql://"):
        from sqlalchemy.pool import NullPool
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"poolclass": NullPool}
    app.config["MEMORIA"] = {}
except Exception as e:
    _boot_errors.append(f"config: {type(e).__name__}: {e}")
    _db_url = "sqlite:///instance/nexora.db"
    app.config["SECRET_KEY"] = "fallback"
    app.config["SQLALCHEMY_DATABASE_URI"] = _db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MEMORIA"] = {}

db.init_app(app)


def _safe_import(module, attr):
    try:
        import importlib
        mod = importlib.import_module(module)
        return getattr(mod, attr)
    except Exception as e:
        _import_errors[module] = f"{type(e).__name__}: {e}"
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
gastos_bp      = _safe_import("routes.gastos",       "gastos_bp")
fiado_bp       = _safe_import("routes.fiado",        "fiado_bp")
sucursales_bp  = _safe_import("routes.sucursales",   "sucursales_bp")

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
app.register_blueprint(sucursales_bp, url_prefix="/api")

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
        from models.sucursal import Sucursal
        from models.compra_insumo import CompraInsumo
        if _db_url.startswith("sqlite"):
            os.makedirs("instance", exist_ok=True)
        db.create_all()

        # Migrations: add new columns to existing tables (safe to re-run)
        from sqlalchemy import text
        migrations = [
            "ALTER TABLE usuario ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'admin'",
            "ALTER TABLE usuario ADD COLUMN IF NOT EXISTS owner_id INTEGER",
            "ALTER TABLE usuario ADD COLUMN IF NOT EXISTS sucursal_id INTEGER",
            "ALTER TABLE product ADD COLUMN IF NOT EXISTS sucursal_id INTEGER",
            "ALTER TABLE sale ADD COLUMN IF NOT EXISTS sucursal_id INTEGER",
            "ALTER TABLE insumo ADD COLUMN IF NOT EXISTS sucursal_id INTEGER",
            "ALTER TABLE gasto ADD COLUMN IF NOT EXISTS sucursal_id INTEGER",
            "ALTER TABLE pedido ADD COLUMN IF NOT EXISTS sucursal_id INTEGER",
            "ALTER TABLE fiado ADD COLUMN IF NOT EXISTS sucursal_id INTEGER",
            "ALTER TABLE client ADD COLUMN IF NOT EXISTS sucursal_id INTEGER",
            "ALTER TABLE production_log ADD COLUMN IF NOT EXISTS sucursal_id INTEGER",
            "ALTER TABLE production_log ADD COLUMN IF NOT EXISTS unidad VARCHAR(20)",
            "ALTER TABLE product ADD COLUMN IF NOT EXISTS rendimiento FLOAT",
            "ALTER TABLE product ADD COLUMN IF NOT EXISTS unidad VARCHAR(20) NOT NULL DEFAULT 'u'",
            "ALTER TABLE sale ADD COLUMN IF NOT EXISTS unidad VARCHAR(20)",
            "ALTER TABLE insumo ADD COLUMN IF NOT EXISTS dias_restock INTEGER",
            "ALTER TABLE insumo ADD COLUMN IF NOT EXISTS qty_restock FLOAT",
            "ALTER TABLE insumo ADD COLUMN IF NOT EXISTS ultimo_pedido TIMESTAMP",
            "ALTER TABLE compra_insumo ADD COLUMN IF NOT EXISTS estado VARCHAR(20) DEFAULT 'llegado'",
            "ALTER TABLE compra_insumo ADD COLUMN IF NOT EXISTS fecha_esperada TIMESTAMP",
            "ALTER TABLE sale ALTER COLUMN product_id DROP NOT NULL",
        ]
        # Type changes (safe: INTEGER fits in FLOAT with no data loss)
        type_migrations = [
            "ALTER TABLE product ALTER COLUMN stock TYPE FLOAT USING stock::FLOAT",
            "ALTER TABLE sale ALTER COLUMN cantidad TYPE FLOAT USING cantidad::FLOAT",
            "ALTER TABLE production_log ALTER COLUMN cantidad TYPE FLOAT USING cantidad::FLOAT",
        ]
        if _db_url.startswith("postgresql://"):
            for sql in type_migrations:
                try:
                    db.session.execute(text(sql))
                    db.session.commit()
                except Exception:
                    db.session.rollback()
        migrations = migrations + []  # keep existing list separate
        if _db_url.startswith("postgresql://"):
            for sql in migrations:
                try:
                    db.session.execute(text(sql))
                except Exception:
                    pass
            db.session.commit()

except Exception as e:
    _startup_error = f"{type(e).__name__}: {e}"
    logging.error(f"DB startup error: {e}")


@app.route("/health")
def health():
    return jsonify({
        "ok":            not (_boot_errors or _import_errors or _startup_error),
        "boot_errors":   _boot_errors,
        "import_errors": _import_errors,
        "startup_error": _startup_error,
        "python":        sys.version,
        "db":            _db_url.split("@")[-1] if "@" in _db_url else "sqlite",
    })


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
