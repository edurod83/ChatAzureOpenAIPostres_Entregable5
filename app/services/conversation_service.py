"""
app/services/conversation_service.py
=====================================
Lógica de negocio para gestionar conversaciones.
Desacoplado de las rutas FastAPI para facilitar las pruebas.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.schemas.conversation import ConversationCreate

logger = logging.getLogger(__name__)


def create_conversation(db: Session, data: ConversationCreate) -> Conversation:
    """Crea y persiste una nueva conversación."""
    conversation = Conversation(title=data.title or "Nueva conversación")
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    logger.info("Conversación creada: id=%d title=%r", conversation.id, conversation.title)
    return conversation


def get_conversation(db: Session, conversation_id: int) -> Optional[Conversation]:
    """Devuelve una conversación por su ID, o None si no existe."""
    return db.query(Conversation).filter(Conversation.id == conversation_id).first()


def get_all_conversations(db: Session) -> List[Conversation]:
    """Devuelve todas las conversaciones ordenadas por última actualización (desc)."""
    return (
        db.query(Conversation)
        .order_by(Conversation.updated_at.desc())
        .all()
    )


def update_conversation_title(
    db: Session, conversation_id: int, title: str
) -> Optional[Conversation]:
    """Actualiza el título y el timestamp updated_at de una conversación."""
    conversation = get_conversation(db, conversation_id)
    if not conversation:
        return None
    conversation.title = title
    conversation.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(conversation)
    logger.info("Título actualizado: id=%d title=%r", conversation_id, title)
    return conversation


def touch_conversation(db: Session, conversation_id: int) -> None:
    """Actualiza únicamente el campo updated_at sin cambiar el título."""
    conversation = get_conversation(db, conversation_id)
    if conversation:
        conversation.updated_at = datetime.now(timezone.utc)
        db.commit()


def delete_conversation(db: Session, conversation_id: int) -> bool:
    """Elimina una conversación (y sus mensajes por cascade)."""
    conversation = get_conversation(db, conversation_id)
    if not conversation:
        return False
    db.delete(conversation)
    db.commit()
    logger.info("Conversación eliminada: id=%d", conversation_id)
    return True
