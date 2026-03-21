"""
app/routes/api.py
=================
API JSON utilizada por el frontend JavaScript para enviar mensajes
sin recargar la página completa.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.conversation import ConversationResponse, ConversationWithMessages
from app.schemas.message import SendMessageRequest
from app.services import conversation_service, message_service
from app.services.openai_service import openai_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(db: Session = Depends(get_db)):
    """Devuelve la lista de conversaciones (sin mensajes)."""
    return conversation_service.get_all_conversations(db)


@router.get(
    "/conversations/{conversation_id}", response_model=ConversationWithMessages
)
async def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """Devuelve una conversación con todos sus mensajes."""
    conv = conversation_service.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    return conv


@router.post("/conversations/{conversation_id}/messages")
async def send_message_api(
    conversation_id: int,
    body: SendMessageRequest,
    db: Session = Depends(get_db),
):
    """
    Envía un mensaje, llama al modelo y devuelve ambos mensajes (usuario y
    asistente) en JSON. Usado por el frontend JS para actualizar el DOM sin
    recargar la página.
    """
    conv = conversation_service.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    # 1. Persistir mensaje del usuario
    user_msg = message_service.create_message(
        db, conversation_id, "user", body.content
    )

    # 2. Construir contexto completo (incluye el mensaje recién guardado)
    all_messages = message_service.get_messages_by_conversation(db, conversation_id)
    payload = [{"role": m.role, "content": m.content} for m in all_messages]

    # 3. Llamar al modelo
    ai_text = "Lo siento, no pude obtener una respuesta. Inténtalo de nuevo."
    error: str | None = None
    try:
        ai_text = openai_service.chat_completion(payload)
    except RuntimeError as exc:
        logger.warning("Error OpenAI (api): %s", exc)
        ai_text = str(exc)
        error = str(exc)

    # 4. Persistir respuesta del asistente
    assistant_msg = message_service.create_message(
        db, conversation_id, "assistant", ai_text
    )

    # 5. Actualizar conversación
    new_title: str | None = None
    if len(all_messages) == 1:  # Primer mensaje → generar título
        new_title = body.content[:60] + ("…" if len(body.content) > 60 else "")
        conversation_service.update_conversation_title(db, conversation_id, new_title)
    else:
        conversation_service.touch_conversation(db, conversation_id)

    return {
        "user_message": {
            "id": user_msg.id,
            "role": user_msg.role,
            "content": user_msg.content,
            "created_at": user_msg.created_at.isoformat(),
        },
        "assistant_message": {
            "id": assistant_msg.id,
            "role": assistant_msg.role,
            "content": assistant_msg.content,
            "created_at": assistant_msg.created_at.isoformat(),
        },
        "new_title": new_title,
        "error": error,
    }
