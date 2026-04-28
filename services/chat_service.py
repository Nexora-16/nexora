from services.ia_service import preguntar_ia
from services.context_service import construir_contexto
from models.chat_message import ChatMessage
from config_db import db


def responder(mensaje, user_id, memoria):
    if user_id not in memoria:
        memoria[user_id] = []
        historial = ChatMessage.query.filter_by(user_id=user_id).order_by(ChatMessage.created_at).all()
        for m in historial:
            memoria[user_id].append({"rol": m.role, "mensaje": m.content})

    db.session.add(ChatMessage(user_id=user_id, role="user", content=mensaje))
    db.session.commit()

    memoria[user_id].append({"rol": "user", "mensaje": mensaje})
    contexto = construir_contexto(user_id, mensaje)
    respuesta = preguntar_ia(contexto, mensaje)

    db.session.add(ChatMessage(user_id=user_id, role="ia", content=respuesta))
    db.session.commit()

    memoria[user_id].append({"rol": "ia", "mensaje": respuesta})
    return respuesta
