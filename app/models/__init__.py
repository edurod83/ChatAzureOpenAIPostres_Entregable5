"""
app/models/__init__.py
======================
Re-exporta los modelos para que Alembic los detecte automáticamente
al inspeccionar Base.metadata.
"""

from app.models.conversation import Conversation  # noqa: F401
from app.models.message import Message            # noqa: F401

__all__ = ["Conversation", "Message"]
