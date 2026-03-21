"""
app/schemas/conversation.py
============================
Schemas Pydantic para validación y serialización de conversaciones.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.message import MessageResponse


class ConversationCreate(BaseModel):
    """Datos para crear una nueva conversación."""

    title: Optional[str] = "Nueva conversación"


class ConversationUpdate(BaseModel):
    """Datos permitidos para actualizar una conversación."""

    title: Optional[str] = None


class ConversationResponse(BaseModel):
    """Representación pública de una conversación (sin mensajes)."""

    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationWithMessages(ConversationResponse):
    """Conversación junto con todos sus mensajes."""

    messages: List[MessageResponse] = []
