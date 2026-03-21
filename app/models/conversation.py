"""
app/models/conversation.py
==========================
Modelo ORM para la tabla `conversations`.
Una conversación agrupa N mensajes.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, default="Nueva conversación")

    # Timestamps con zona horaria
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relación 1:N → mensajes ordenados por fecha de creación
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Conversation id={self.id} title={self.title!r}>"
