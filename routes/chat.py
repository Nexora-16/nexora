from flask import Blueprint, request, jsonify, current_app, g
from services.chat_service import responder
from models.chat_message import ChatMessage
from config_db import db
from utils.auth_utils import require_auth, require_admin

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/chat", methods=["POST"])
@require_auth
@require_admin
def chat():
    data = request.get_json(silent=True) or {}
    mensaje = (data.get("mensaje") or "").strip()
    if not mensaje:
        return jsonify({"msg": "El mensaje no puede estar vacío"}), 400

    memoria = current_app.config["MEMORIA"]
    respuesta = responder(mensaje, g.owner_id, memoria)
    return jsonify({"respuesta": respuesta})


@chat_bp.route("/chat/history", methods=["GET"])
@require_auth
@require_admin
def chat_history():
    mensajes = ChatMessage.query.filter_by(user_id=g.owner_id).order_by(ChatMessage.created_at).all()
    return jsonify([{"role": m.role, "content": m.content} for m in mensajes])


@chat_bp.route("/chat/history", methods=["DELETE"])
@require_auth
@require_admin
def limpiar_chat():
    ChatMessage.query.filter_by(user_id=g.owner_id).delete()
    db.session.commit()
    if g.owner_id in current_app.config["MEMORIA"]:
        del current_app.config["MEMORIA"][g.owner_id]
    return jsonify({"msg": "Historial eliminado"})
