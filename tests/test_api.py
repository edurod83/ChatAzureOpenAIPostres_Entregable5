"""
tests/test_api.py
=================
Pruebas unitarias sencillas — sin conexión a base de datos.
Validan schemas Pydantic de la aplicación.
"""

from pydantic import ValidationError
import pytest

from app.schemas.conversation import ConversationCreate, ConversationUpdate
from app.schemas.message import MessageCreate, SendMessageRequest


def test_conversation_schema_defaults():
    """ConversationCreate tiene título por defecto."""
    conv = ConversationCreate()
    assert conv.title == "Nueva conversación"


def test_conversation_update_optional():
    """ConversationUpdate permite título None."""
    update = ConversationUpdate()
    assert update.title is None
    update2 = ConversationUpdate(title="Nuevo título")
    assert update2.title == "Nuevo título"


def test_message_schema_rejects_empty():
    """MessageCreate rechaza contenido vacío."""
    with pytest.raises(ValidationError):
        MessageCreate(content="   ", role="user")


def test_send_message_request_valid():
    """SendMessageRequest acepta contenido válido."""
    msg = SendMessageRequest(content="Hola, ¿cómo estás?")
    assert msg.content == "Hola, ¿cómo estás?"
