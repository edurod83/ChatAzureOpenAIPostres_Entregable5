"""
app/services/message_service.py
================================
Lógica de negocio para gestionar mensajes.
"""

import logging
from typing import List

from sqlalchemy.orm import Session

from app.models.message import Message

logger = logging.getLogger(__name__)


def create_message(
    db: Session, conversation_id: int, role: str, content: str
) -> Message:
    """Crea y persiste un nuevo mensaje en la conversación indicada."""
    message = Message(conversation_id=conversation_id, role=role, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    logger.debug(
        "Mensaje creado: id=%d conv=%d role=%s", message.id, conversation_id, role
    )
    return message


def get_messages_by_conversation(db: Session, conversation_id: int) -> List[Message]:
    """Devuelve todos los mensajes de una conversación, ordenados por fecha."""
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .all()
    )
