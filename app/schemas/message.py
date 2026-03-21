"""
app/schemas/message.py
======================
Schemas Pydantic para validación y serialización de mensajes.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator


class MessageCreate(BaseModel):
    """Datos necesarios para crear un mensaje (uso interno)."""

    content: str
    role: Literal["user", "assistant", "system"] = "user"

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El contenido del mensaje no puede estar vacío.")
        return v


class MessageResponse(BaseModel):
    """Representación pública de un mensaje."""

    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SendMessageRequest(BaseModel):
    """Cuerpo de la petición JSON para enviar un mensaje vía API."""

    content: str

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El contenido del mensaje no puede estar vacío.")
        return v
