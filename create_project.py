"""
create_project.py
=================
Script de bootstrapping del proyecto Azure AI Chat.
Ejecuta este script UNA SOLA VEZ desde el directorio raíz del proyecto:

    python create_project.py

Creará todos los directorios y ficheros del proyecto.
"""

import os
import sys
import textwrap

BASE = os.path.dirname(os.path.abspath(__file__))


def write(rel_path: str, content: str) -> None:
    """Crea directorios necesarios y escribe el fichero."""
    full = os.path.join(BASE, rel_path.replace("/", os.sep))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✓  {rel_path}")


# ══════════════════════════════════════════════════════════════════════════════
#  FICHEROS DE CONFIGURACIÓN DEL PROYECTO
# ══════════════════════════════════════════════════════════════════════════════

ALEMBIC_INI = """\
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

# La URL real se sobreescribe en alembic/env.py con la variable de entorno
sqlalchemy.url = driver://user:pass@localhost/dbname

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""

# ══════════════════════════════════════════════════════════════════════════════
#  APP PACKAGE
# ══════════════════════════════════════════════════════════════════════════════

APP_INIT = "# Paquete raíz de la aplicación\n"

APP_MAIN = '''\
"""
app/main.py
===========
Punto de entrada de la aplicación FastAPI.
Registra middlewares, rutas y manejadores de errores globales.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.routes import api, chat

# Configurar logging antes que cualquier otra cosa
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación (startup / shutdown)."""
    logger.info("Iniciando %s...", settings.APP_NAME)
    yield
    logger.info("Cerrando %s.", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    description="Chat de IA con Azure OpenAI y PostgreSQL",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.DEBUG,
)

# Archivos estáticos (CSS, JS, imágenes)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Rutas de la interfaz web (HTML / Jinja2)
app.include_router(chat.router, tags=["chat"])

# Rutas de la API JSON (usadas por el frontend vía fetch)
app.include_router(api.router, prefix="/api", tags=["api"])


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Captura cualquier excepción no controlada y devuelve JSON 500."""
    logger.error("Error no controlado en %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor. Por favor, inténtalo de nuevo."},
    )
'''

# ── core ──────────────────────────────────────────────────────────────────────

CORE_INIT = "# Paquete core: configuración y logging\n"

CORE_CONFIG = '''\
"""
app/core/config.py
==================
Configuración centralizada de la aplicación.
Todas las variables se leen desde el fichero .env o variables de entorno.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Base de datos ──────────────────────────────────────────────────────
    DATABASE_URL: str

    # ── Azure OpenAI ───────────────────────────────────────────────────────
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"
    AZURE_OPENAI_DEPLOYMENT: str

    # ── Aplicación ─────────────────────────────────────────────────────────
    APP_NAME: str = "Azure AI Chat"
    DEBUG: bool = False

    # Prompt del sistema enviado como primer mensaje a OpenAI
    SYSTEM_PROMPT: str = (
        "Eres un asistente de IA útil, claro y conciso. "
        "Responde en el mismo idioma que el usuario."
    )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


# Instancia global; importar desde aquí en el resto de módulos
settings = Settings()
'''

CORE_LOGGING = '''\
"""
app/core/logging_config.py
==========================
Configura el sistema de logging de la aplicación.
"""

import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """Configura handlers y formato para el logger raíz."""
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=level,
        format=fmt,
        datefmt=date_fmt,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Reducir verbosidad de librerías externas
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
'''

# ── db ────────────────────────────────────────────────────────────────────────

DB_INIT = "# Paquete db: motor y sesión de SQLAlchemy\n"

DB_BASE = '''\
"""
app/db/base.py
==============
Clase base declarativa de SQLAlchemy.
Todos los modelos deben heredar de Base.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Clase base para todos los modelos ORM."""
    pass
'''

DB_SESSION = '''\
"""
app/db/session.py
=================
Crea el motor de base de datos y la fábrica de sesiones.
Expone la dependencia `get_db` para inyectar en endpoints FastAPI.
"""

import logging
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,   # Verifica la conexión antes de cada uso
    pool_size=5,
    max_overflow=10,
    echo=settings.DEBUG,  # Muestra SQL en modo debug
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependencia FastAPI.
    Abre una sesión de base de datos y la cierra al finalizar la request.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
'''

# ── models ────────────────────────────────────────────────────────────────────

MODELS_INIT = '''\
"""
app/models/__init__.py
======================
Re-exporta los modelos para que Alembic los detecte automáticamente
al inspeccionar Base.metadata.
"""

from app.models.conversation import Conversation  # noqa: F401
from app.models.message import Message            # noqa: F401

__all__ = ["Conversation", "Message"]
'''

MODELS_CONVERSATION = '''\
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
'''

MODELS_MESSAGE = '''\
"""
app/models/message.py
=====================
Modelo ORM para la tabla `messages`.
Cada mensaje pertenece a una conversación y tiene un rol.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Valores válidos: "user" | "assistant" | "system"
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relación inversa con la conversación
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message id={self.id} role={self.role!r} conv={self.conversation_id}>"
'''

# ── schemas ───────────────────────────────────────────────────────────────────

SCHEMAS_INIT = "# Paquete schemas: validación y serialización Pydantic\n"

SCHEMAS_MESSAGE = '''\
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
'''

SCHEMAS_CONVERSATION = '''\
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
'''

# ── services ──────────────────────────────────────────────────────────────────

SERVICES_INIT = "# Paquete services: lógica de negocio\n"

SERVICES_CONVERSATION = '''\
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
'''

SERVICES_MESSAGE = '''\
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
'''

SERVICES_OPENAI = '''\
"""
app/services/openai_service.py
==============================
Servicio desacoplado para interactuar con Azure OpenAI.
Encapsula el cliente, la configuración y el manejo de errores,
de forma que las rutas no necesitan conocer los detalles de la API.
"""

import logging
from typing import Dict, List, Optional

from openai import APIConnectionError, APIStatusError, APITimeoutError, AzureOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class AzureOpenAIService:
    """Cliente Azure OpenAI con manejo de errores y prompt de sistema."""

    def __init__(self) -> None:
        self._client: Optional[AzureOpenAI] = None
        self.deployment = settings.AZURE_OPENAI_DEPLOYMENT
        self.system_prompt = settings.SYSTEM_PROMPT

    @property
    def client(self) -> AzureOpenAI:
        """Inicialización lazy del cliente para facilitar las pruebas."""
        if self._client is None:
            self._client = AzureOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
            )
        return self._client

    def chat_completion(self, messages: List[Dict[str, str]]) -> str:
        """
        Envía el historial de mensajes al modelo y devuelve la respuesta.

        Args:
            messages: Lista de dicts con las claves 'role' y 'content'.

        Returns:
            Texto de respuesta del asistente.

        Raises:
            RuntimeError: Si ocurre un error irrecuperable de la API.
        """
        # Insertar el prompt de sistema si no viene ya incluido
        full_messages: List[Dict[str, str]] = []
        if not messages or messages[0].get("role") != "system":
            full_messages.append({"role": "system", "content": self.system_prompt})
        full_messages.extend(messages)

        logger.info(
            "Llamando Azure OpenAI: deployment=%s, mensajes=%d",
            self.deployment,
            len(full_messages),
        )

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=full_messages,  # type: ignore[arg-type]
                temperature=0.7,
                max_tokens=2000,
                timeout=60,
            )
            content = response.choices[0].message.content or ""
            tokens = response.usage.total_tokens if response.usage else "?"
            logger.info("Respuesta recibida (tokens=%s)", tokens)
            return content

        except APIConnectionError as e:
            logger.error("Error de conexión con Azure OpenAI: %s", e)
            raise RuntimeError(
                "No se pudo conectar con el servicio de IA. "
                "Verifica el endpoint y la clave de API."
            ) from e

        except APITimeoutError as e:
            logger.error("Timeout al llamar a Azure OpenAI: %s", e)
            raise RuntimeError(
                "El servicio de IA tardó demasiado en responder. "
                "Inténtalo de nuevo."
            ) from e

        except APIStatusError as e:
            logger.error(
                "Error de estado de Azure OpenAI (status=%d): %s",
                e.status_code,
                e.message,
            )
            raise RuntimeError(
                f"Error del servicio de IA (código {e.status_code}). "
                "Inténtalo de nuevo."
            ) from e


# Instancia singleton; se inicializa de forma lazy al primer uso
openai_service = AzureOpenAIService()
'''

# ── routes ────────────────────────────────────────────────────────────────────

ROUTES_INIT = "# Paquete routes: endpoints FastAPI\n"

ROUTES_CHAT = '''\
"""
app/routes/chat.py
==================
Rutas de la interfaz web: devuelven HTML renderizado con Jinja2.
El envío de mensajes también tiene un endpoint de formulario aquí
(fallback sin JavaScript).
"""

import logging

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.conversation import ConversationCreate
from app.services import conversation_service, message_service
from app.services.openai_service import openai_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    """Vista de bienvenida con la lista de conversaciones en el sidebar."""
    conversations = conversation_service.get_all_conversations(db)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "conversations": conversations,
            "active_conversation": None,
        },
    )


@router.post("/conversations/new")
async def create_conversation(db: Session = Depends(get_db)):
    """Crea una conversación vacía y redirige a ella."""
    conv = conversation_service.create_conversation(db, ConversationCreate())
    return RedirectResponse(url=f"/conversations/{conv.id}", status_code=303)


@router.get("/conversations/{conversation_id}", response_class=HTMLResponse)
async def view_conversation(
    conversation_id: int, request: Request, db: Session = Depends(get_db)
):
    """Muestra el historial de una conversación concreta."""
    conversations = conversation_service.get_all_conversations(db)
    conversation = conversation_service.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    messages = message_service.get_messages_by_conversation(db, conversation_id)
    return templates.TemplateResponse(
        "conversation.html",
        {
            "request": request,
            "conversations": conversations,
            "active_conversation": conversation,
            "messages": messages,
        },
    )


@router.post("/conversations/{conversation_id}/messages")
async def send_message_form(
    conversation_id: int,
    content: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Fallback para envío de mensajes sin JavaScript (formulario HTML estándar).
    El frontend con JS usa el endpoint JSON /api/conversations/{id}/messages.
    """
    conversation = conversation_service.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    content = content.strip()
    if not content:
        return RedirectResponse(url=f"/conversations/{conversation_id}", status_code=303)

    # 1. Persistir mensaje del usuario
    message_service.create_message(db, conversation_id, "user", content)

    # 2. Construir contexto completo para el modelo
    all_messages = message_service.get_messages_by_conversation(db, conversation_id)
    payload = [{"role": m.role, "content": m.content} for m in all_messages]

    # 3. Obtener respuesta del modelo
    ai_text = "Lo siento, no pude obtener una respuesta. Inténtalo de nuevo."
    try:
        ai_text = openai_service.chat_completion(payload)
    except RuntimeError as exc:
        logger.warning("Error OpenAI (form): %s", exc)
        ai_text = str(exc)

    # 4. Persistir respuesta del asistente
    message_service.create_message(db, conversation_id, "assistant", ai_text)

    # 5. Actualizar título si es el primer intercambio
    if len(all_messages) == 1:
        title = content[:60] + ("\u2026" if len(content) > 60 else "")
        conversation_service.update_conversation_title(db, conversation_id, title)
    else:
        conversation_service.touch_conversation(db, conversation_id)

    return RedirectResponse(url=f"/conversations/{conversation_id}", status_code=303)


@router.post("/conversations/{conversation_id}/delete")
async def delete_conversation(
    conversation_id: int, db: Session = Depends(get_db)
):
    """Elimina una conversación y redirige a la vista principal."""
    conversation_service.delete_conversation(db, conversation_id)
    return RedirectResponse(url="/", status_code=303)
'''

ROUTES_API = '''\
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
        new_title = body.content[:60] + ("\u2026" if len(body.content) > 60 else "")
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
'''

# ══════════════════════════════════════════════════════════════════════════════
#  TEMPLATES JINJA2
# ══════════════════════════════════════════════════════════════════════════════

TEMPLATE_BASE = """\
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{% block title %}Azure AI Chat{% endblock %}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link
    href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap"
    rel="stylesheet"
  />
  <link rel="stylesheet" href="/static/css/styles.css" />
</head>
<body>
  <div class="app-container">

    <!-- ═══ BARRA LATERAL ═══════════════════════════════════════════════════ -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="brand">
          <!-- Icono de la marca -->
          <svg class="brand-icon" viewBox="0 0 32 32" fill="none">
            <circle cx="16" cy="16" r="14" stroke="currentColor" stroke-width="1.8"/>
            <path d="M10 16c0-3.314 2.686-6 6-6s6 2.686 6 6-2.686 6-6 6"
                  stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <circle cx="16" cy="16" r="3" fill="currentColor"/>
          </svg>
          <span class="brand-name">Azure AI Chat</span>
        </div>

        <!-- Botón nueva conversación -->
        <form action="/conversations/new" method="post">
          <button type="submit" class="btn-new-chat">
            <svg viewBox="0 0 24 24" fill="none">
              <path d="M12 5v14M5 12h14" stroke="currentColor"
                    stroke-width="2" stroke-linecap="round"/>
            </svg>
            <span>Nueva conversación</span>
          </button>
        </form>
      </div>

      <div class="sidebar-content">
        <p class="conversations-label">Conversaciones recientes</p>
        <nav class="conversations-list">
          {% for conv in conversations %}
          <div class="conversation-item
               {% if active_conversation and active_conversation.id == conv.id %}active{% endif %}">

            <a href="/conversations/{{ conv.id }}" class="conversation-link">
              <span class="conversation-title">{{ conv.title }}</span>
              <span class="conversation-date">
                {{ conv.updated_at.strftime('%d/%m %H:%M') }}
              </span>
            </a>

            <form action="/conversations/{{ conv.id }}/delete" method="post"
                  class="delete-form"
                  onsubmit="return confirm('¿Eliminar esta conversación?')">
              <button type="submit" class="btn-delete" title="Eliminar conversación">
                <svg viewBox="0 0 24 24" fill="none">
                  <path d="M18 6L6 18M6 6l12 12" stroke="currentColor"
                        stroke-width="2" stroke-linecap="round"/>
                </svg>
              </button>
            </form>
          </div>
          {% else %}
          <div class="no-conversations">
            <p>Aún no hay conversaciones.</p>
            <p>¡Empieza una nueva!</p>
          </div>
          {% endfor %}
        </nav>
      </div>
    </aside>

    <!-- ═══ CONTENIDO PRINCIPAL ════════════════════════════════════════════ -->
    <main class="main-content">
      {% block content %}{% endblock %}
    </main>

  </div><!-- /.app-container -->

  <script src="/static/js/chat.js"></script>
  {% block extra_scripts %}{% endblock %}
</body>
</html>
"""

TEMPLATE_INDEX = """\
{% extends "base.html" %}

{% block title %}Azure AI Chat{% endblock %}

{% block content %}
<div class="welcome-screen">
  <div class="welcome-content">

    <!-- Logo animado -->
    <div class="welcome-icon">
      <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="wg" x1="0" y1="0" x2="100" y2="100"
                          gradientUnits="userSpaceOnUse">
            <stop stop-color="#6366f1"/>
            <stop offset="1" stop-color="#06b6d4"/>
          </linearGradient>
        </defs>
        <circle cx="50" cy="50" r="46" stroke="url(#wg)" stroke-width="2.5"/>
        <path d="M32 50c0-9.941 8.059-18 18-18s18 8.059 18 18-8.059 18-18 18"
              stroke="url(#wg)" stroke-width="3" stroke-linecap="round"/>
        <circle cx="50" cy="50" r="7" fill="url(#wg)"/>
        <path d="M50 28v-8M50 80v-8M28 50h-8M80 50h-8"
              stroke="url(#wg)" stroke-width="2.5" stroke-linecap="round"
              opacity="0.4"/>
      </svg>
    </div>

    <h1 class="welcome-title">Hola, ¿en qué puedo ayudarte?</h1>
    <p class="welcome-subtitle">Conectado a Azure OpenAI · Conversaciones guardadas en PostgreSQL</p>

    <div class="welcome-actions">
      <form action="/conversations/new" method="post">
        <button type="submit" class="btn-start">
          <svg viewBox="0 0 24 24" fill="none">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"
                  stroke="currentColor" stroke-width="2"
                  stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Comenzar conversación
        </button>
      </form>
    </div>

    <div class="welcome-features">
      <div class="feature">
        <span class="feature-icon">💬</span>
        <span>Historial persistente</span>
      </div>
      <div class="feature">
        <span class="feature-icon">⚡</span>
        <span>Respuestas en tiempo real</span>
      </div>
      <div class="feature">
        <span class="feature-icon">🔒</span>
        <span>Azure OpenAI</span>
      </div>
    </div>

  </div>
</div>
{% endblock %}
"""

TEMPLATE_CONVERSATION = """\
{% extends "base.html" %}

{% block title %}{{ active_conversation.title }} — Azure AI Chat{% endblock %}

{% block content %}
<div class="chat-container">

  <!-- Cabecera -->
  <header class="chat-header">
    <div class="chat-header-info">
      <h2 class="chat-title" id="chatTitle">{{ active_conversation.title }}</h2>
      <span class="chat-meta">
        Creada el {{ active_conversation.created_at.strftime('%d/%m/%Y a las %H:%M') }}
      </span>
    </div>
  </header>

  <!-- Área de mensajes -->
  <div class="messages-area" id="messagesArea">

    {% if messages %}
      {% for message in messages %}
      <div class="message message--{{ message.role }}" id="msg-{{ message.id }}">
        <div class="message-bubble">
          <div class="message-content">{{ message.content }}</div>
          <div class="message-time">
            {% if message.role == 'user' %}
            <svg viewBox="0 0 24 24" fill="none" class="role-icon">
              <circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="1.5"/>
              <path d="M4 20c0-4 3.582-7 8-7s8 3 8 7"
                    stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
            {% else %}
            <svg viewBox="0 0 24 24" fill="none" class="role-icon">
              <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.5"/>
              <path d="M8 12h8M12 8v8"
                    stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
            {% endif %}
            {{ message.created_at.strftime('%H:%M') }}
          </div>
        </div>
      </div>
      {% endfor %}

    {% else %}
    <div class="empty-messages" id="emptyState">
      <div class="empty-icon">
        <svg viewBox="0 0 64 64" fill="none">
          <path d="M56 40a8 8 0 0 1-8 8H16l-8 8V16a8 8 0 0 1 8-8h32a8 8 0 0 1 8 8z"
                stroke="currentColor" stroke-width="2"
                stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M22 28h20M22 36h12"
                stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </div>
      <p>Esta conversación está vacía.</p>
      <p>¡Envía tu primer mensaje para comenzar!</p>
    </div>
    {% endif %}

    <!-- Indicador de escritura del asistente -->
    <div class="typing-indicator" id="typingIndicator" style="display:none;">
      <div class="message message--assistant">
        <div class="message-bubble">
          <div class="typing-dots">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>

  </div><!-- /.messages-area -->

  <!-- Área de entrada -->
  <div class="input-area">
    <form
      id="messageForm"
      class="message-form"
      action="/conversations/{{ active_conversation.id }}/messages"
      method="post"
      data-conversation-id="{{ active_conversation.id }}"
    >
      <div class="input-wrapper">
        <textarea
          id="messageInput"
          name="content"
          class="message-input"
          placeholder="Escribe un mensaje…"
          rows="1"
          autocomplete="off"
          required
        ></textarea>
        <button type="submit" class="btn-send" id="sendButton" title="Enviar (Enter)">
          <svg viewBox="0 0 24 24" fill="none">
            <path d="M22 2L11 13M22 2L15 22l-4-9-9-4 20-7z"
                  stroke="currentColor" stroke-width="2"
                  stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
      <p class="input-hint">
        <kbd>Enter</kbd> para enviar &nbsp;·&nbsp;
        <kbd>Shift + Enter</kbd> para nueva línea
      </p>
    </form>
  </div>

</div><!-- /.chat-container -->
{% endblock %}

{% block extra_scripts %}
<script>
  /* Exponer el ID de conversación al módulo chat.js */
  window.CONVERSATION_ID = {{ active_conversation.id }};
</script>
{% endblock %}
"""

# ══════════════════════════════════════════════════════════════════════════════
#  CSS
# ══════════════════════════════════════════════════════════════════════════════

STYLES_CSS = """\
/* ═══════════════════════════════════════════════════════════════════════════
   Azure AI Chat — Hoja de estilos principal
   Diseño tipo Gemini: sidebar oscuro + área de chat clara.
   ═══════════════════════════════════════════════════════════════════════════ */

/* ── Variables de diseño ───────────────────────────────────────────────── */
:root {
  --sidebar-width: 280px;
  --sidebar-bg:    #1e1e2e;
  --sidebar-hover: #2a2a3e;
  --sidebar-active:#2d2d44;
  --sidebar-text:  #cdd6f4;
  --sidebar-muted: #6c7086;
  --sidebar-border:#313244;

  --main-bg:   #f5f5f7;
  --chat-bg:   #ffffff;

  --user-bg:   #6366f1;
  --user-text: #ffffff;
  --ai-bg:     #ffffff;
  --ai-text:   #1e1e2e;
  --ai-border: #e5e7eb;

  --accent:       #6366f1;
  --accent-hover: #4f46e5;
  --danger:       #f38ba8;

  --text-primary:   #1e1e2e;
  --text-secondary: #4b5563;
  --text-muted:     #9ca3af;

  --input-border:  #e5e7eb;
  --input-focus:   #6366f1;
  --input-focus-shadow: rgba(99,102,241,0.15);

  --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --radius:    12px;
  --radius-sm: 6px;
  --shadow:    0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.05);
  --shadow-md: 0 4px 6px -1px rgba(0,0,0,.1), 0 2px 4px -1px rgba(0,0,0,.06);
}

/* ── Reset ─────────────────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body {
  height: 100%;
  font-family: var(--font);
  font-size: 15px;
  line-height: 1.6;
  color: var(--text-primary);
  background: var(--main-bg);
  -webkit-font-smoothing: antialiased;
}

/* ── Layout raíz ───────────────────────────────────────────────────────── */
.app-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* ══════════════════════════════════════════════════════════════════════════
   SIDEBAR
   ══════════════════════════════════════════════════════════════════════════ */
.sidebar {
  width: var(--sidebar-width);
  background: var(--sidebar-bg);
  color: var(--sidebar-text);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  border-right: 1px solid var(--sidebar-border);
  overflow: hidden;
}

/* Cabecera del sidebar */
.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid var(--sidebar-border);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 2px 0;
  user-select: none;
}
.brand-icon {
  width: 26px; height: 26px;
  color: var(--accent);
  flex-shrink: 0;
}
.brand-name {
  font-size: 14.5px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--sidebar-text);
}

.btn-new-chat {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 9px 14px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-family: var(--font);
  font-size: 13.5px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-new-chat:hover { background: var(--accent-hover); }
.btn-new-chat svg { width: 16px; height: 16px; flex-shrink: 0; }

/* Lista de conversaciones */
.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 10px 8px;
  scrollbar-width: thin;
  scrollbar-color: var(--sidebar-border) transparent;
}
.sidebar-content::-webkit-scrollbar { width: 4px; }
.sidebar-content::-webkit-scrollbar-thumb {
  background: var(--sidebar-border);
  border-radius: 2px;
}

.conversations-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--sidebar-muted);
  padding: 4px 8px 8px;
}

.conversations-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.conversation-item {
  display: flex;
  align-items: stretch;
  border-radius: var(--radius-sm);
  transition: background 0.1s;
  position: relative;
}
.conversation-item:hover                { background: var(--sidebar-hover); }
.conversation-item.active               { background: var(--sidebar-active); }
.conversation-item:hover .btn-delete    { opacity: 1; }

.conversation-link {
  flex: 1;
  padding: 8px 10px;
  text-decoration: none;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.conversation-title {
  font-size: 13.5px;
  color: var(--sidebar-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}
.conversation-date {
  font-size: 11px;
  color: var(--sidebar-muted);
}

.delete-form  { display: flex; }
.btn-delete {
  background: none;
  border: none;
  color: var(--sidebar-muted);
  padding: 0 8px;
  display: flex;
  align-items: center;
  opacity: 0;
  cursor: pointer;
  transition: opacity 0.1s, color 0.1s;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  flex-shrink: 0;
}
.btn-delete:hover { color: var(--danger); }
.btn-delete svg   { width: 14px; height: 14px; }

.no-conversations {
  padding: 20px 10px;
  text-align: center;
  color: var(--sidebar-muted);
  font-size: 13px;
  line-height: 1.8;
}

/* ══════════════════════════════════════════════════════════════════════════
   ÁREA PRINCIPAL
   ══════════════════════════════════════════════════════════════════════════ */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--main-bg);
}

/* ── Pantalla de bienvenida ─────────────────────────────────────────────── */
.welcome-screen {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}
.welcome-content {
  text-align: center;
  max-width: 520px;
}
.welcome-icon {
  margin-bottom: 28px;
}
.welcome-icon svg {
  width: 96px; height: 96px;
  filter: drop-shadow(0 4px 24px rgba(99,102,241,.25));
}
.welcome-title {
  font-size: 30px;
  font-weight: 700;
  letter-spacing: -0.025em;
  color: var(--text-primary);
  margin-bottom: 10px;
}
.welcome-subtitle {
  font-size: 15px;
  color: var(--text-secondary);
  margin-bottom: 36px;
}
.welcome-actions { margin-bottom: 40px; }

.btn-start {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 13px 32px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 999px;
  font-family: var(--font);
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  box-shadow: var(--shadow-md);
  transition: background 0.15s, transform 0.1s;
}
.btn-start:hover { background: var(--accent-hover); transform: translateY(-1px); }
.btn-start svg   { width: 18px; height: 18px; }

.welcome-features {
  display: flex;
  justify-content: center;
  gap: 24px;
  flex-wrap: wrap;
}
.feature {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}
.feature-icon { font-size: 16px; }

/* ══════════════════════════════════════════════════════════════════════════
   CHAT
   ══════════════════════════════════════════════════════════════════════════ */
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* Cabecera del chat */
.chat-header {
  padding: 14px 24px;
  border-bottom: 1px solid var(--input-border);
  background: var(--chat-bg);
  flex-shrink: 0;
}
.chat-title {
  font-size: 15.5px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 80%;
}
.chat-meta {
  font-size: 12px;
  color: var(--text-muted);
}

/* ── Área de mensajes ───────────────────────────────────────────────────── */
.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 28px 32px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  background: var(--main-bg);
  scroll-behavior: smooth;
  scrollbar-width: thin;
  scrollbar-color: #d1d5db transparent;
}
.messages-area::-webkit-scrollbar       { width: 6px; }
.messages-area::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}

/* Estado vacío */
.empty-messages {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--text-muted);
  font-size: 14px;
  text-align: center;
  padding: 60px 20px;
}
.empty-icon svg {
  width: 56px; height: 56px;
  color: #d1d5db;
  margin-bottom: 12px;
}

/* ── Burbujas ───────────────────────────────────────────────────────────── */
.message {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  max-width: 72%;
  animation: fadeInUp 0.2s ease;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0);   }
}

.message--user      { align-self: flex-end;   flex-direction: row-reverse; }
.message--assistant { align-self: flex-start; }
.message--system    { align-self: center; max-width: 60%; }

.message-bubble {
  border-radius: var(--radius);
  padding: 12px 16px;
  box-shadow: var(--shadow);
  word-break: break-word;
  overflow-wrap: anywhere;
}

/* Burbuja del usuario */
.message--user .message-bubble {
  background: var(--user-bg);
  color: var(--user-text);
  border-radius: var(--radius) var(--radius) 4px var(--radius);
}
/* Burbuja del asistente */
.message--assistant .message-bubble {
  background: var(--ai-bg);
  color: var(--ai-text);
  border: 1px solid var(--ai-border);
  border-radius: var(--radius) var(--radius) var(--radius) 4px;
}
/* Burbuja de sistema */
.message--system .message-bubble {
  background: #fef3c7;
  border: 1px solid #fde68a;
  color: #92400e;
  font-size: 13px;
  border-radius: var(--radius);
}

.message-content {
  font-size: 14.5px;
  line-height: 1.7;
  white-space: pre-wrap;
}

.message-time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  margin-top: 6px;
  opacity: 0.65;
}
.message--user      .message-time { justify-content: flex-end; color: rgba(255,255,255,.85); }
.message--assistant .message-time { color: var(--text-muted); }

.role-icon { width: 12px; height: 12px; flex-shrink: 0; }

/* ── Indicador de escritura ─────────────────────────────────────────────── */
.typing-indicator .message--assistant { max-width: none; }

.typing-dots {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 2px;
}
.typing-dots span {
  width: 8px; height: 8px;
  background: var(--text-muted);
  border-radius: 50%;
  animation: bounce 1.2s infinite ease-in-out;
}
.typing-dots span:nth-child(2) { animation-delay: .2s; }
.typing-dots span:nth-child(3) { animation-delay: .4s; }

@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0);   opacity: .4; }
  30%           { transform: translateY(-6px); opacity: 1;  }
}

/* ── Área de entrada ────────────────────────────────────────────────────── */
.input-area {
  padding: 14px 24px 20px;
  background: var(--chat-bg);
  border-top: 1px solid var(--input-border);
  flex-shrink: 0;
}

.message-form {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  background: var(--chat-bg);
  border: 1.5px solid var(--input-border);
  border-radius: var(--radius);
  padding: 10px 12px;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.input-wrapper:focus-within {
  border-color: var(--input-focus);
  box-shadow: 0 0 0 3px var(--input-focus-shadow);
}

.message-input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  font-family: var(--font);
  font-size: 14.5px;
  color: var(--text-primary);
  resize: none;
  max-height: 200px;
  line-height: 1.55;
}
.message-input::placeholder { color: var(--text-muted); }

.btn-send {
  background: var(--accent);
  border: none;
  border-radius: var(--radius-sm);
  color: #fff;
  width: 36px; height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s;
}
.btn-send:hover    { background: var(--accent-hover); }
.btn-send:disabled { background: #d1d5db; cursor: not-allowed; }
.btn-send svg      { width: 15px; height: 15px; }

.input-hint {
  font-size: 11.5px;
  color: var(--text-muted);
  text-align: center;
}
.input-hint kbd {
  font-family: var(--font);
  font-size: 10.5px;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 3px;
  padding: 1px 5px;
}

/* ══════════════════════════════════════════════════════════════════════════
   RESPONSIVE
   ══════════════════════════════════════════════════════════════════════════ */
@media (max-width: 900px) {
  :root { --sidebar-width: 240px; }
  .message { max-width: 85%; }
  .messages-area { padding: 20px; }
}

@media (max-width: 640px) {
  .sidebar {
    position: fixed;
    left: -100%;
    top: 0; bottom: 0;
    z-index: 200;
    transition: left 0.25s ease;
    box-shadow: 4px 0 16px rgba(0,0,0,.3);
  }
  .sidebar.open { left: 0; }

  .message       { max-width: 92%; }
  .messages-area { padding: 16px; }
  .input-area    { padding: 12px 16px 16px; }

  .welcome-title    { font-size: 22px; }
  .welcome-features { gap: 16px; }
}
"""

# ══════════════════════════════════════════════════════════════════════════════
#  JAVASCRIPT
# ══════════════════════════════════════════════════════════════════════════════

CHAT_JS = """\
/**
 * chat.js
 * =======
 * Gestión del chat en el cliente:
 *   - Auto-resize del textarea
 *   - Envío de mensajes con Enter (Shift+Enter = nueva línea)
 *   - Petición AJAX al endpoint /api/conversations/{id}/messages
 *   - Inserción dinámica de burbujas de mensajes en el DOM
 *   - Indicador de escritura mientras el modelo responde
 *   - Actualización del título en el sidebar
 */

(function () {
  "use strict";

  // ── Elementos del DOM ──────────────────────────────────────────────────────
  const form            = document.getElementById("messageForm");
  const input           = document.getElementById("messageInput");
  const sendButton      = document.getElementById("sendButton");
  const messagesArea    = document.getElementById("messagesArea");
  const typingIndicator = document.getElementById("typingIndicator");
  const conversationId  = window.CONVERSATION_ID;

  // Sólo actuar si estamos en la vista de conversación
  if (!form || !input || !messagesArea) return;

  // ── Scroll al último mensaje ───────────────────────────────────────────────
  function scrollToBottom(smooth) {
    messagesArea.scrollTo({
      top: messagesArea.scrollHeight,
      behavior: smooth ? "smooth" : "auto",
    });
  }

  // Scroll inicial sin animación para no mostrar el desplazamiento al cargar
  scrollToBottom(false);

  // ── Auto-resize del textarea ───────────────────────────────────────────────
  function autoResize() {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 200) + "px";
  }
  input.addEventListener("input", autoResize);

  // ── Enter para enviar; Shift+Enter para nueva línea ───────────────────────
  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!sendButton.disabled && input.value.trim()) {
        form.dispatchEvent(new Event("submit", { cancelable: true, bubbles: true }));
      }
    }
  });

  // ── Formateo de hora (HH:MM) ───────────────────────────────────────────────
  function formatTime(isoString) {
    return new Date(isoString).toLocaleTimeString("es-ES", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  // ── Escape de HTML para evitar XSS ────────────────────────────────────────
  function escapeHtml(text) {
    const el = document.createElement("div");
    el.appendChild(document.createTextNode(text));
    return el.innerHTML;
  }

  // ── Construir elemento de burbuja de mensaje ───────────────────────────────
  function buildMessageEl(role, content, timeStr) {
    const userIcon = `
      <svg viewBox="0 0 24 24" fill="none" class="role-icon">
        <circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="1.5"/>
        <path d="M4 20c0-4 3.582-7 8-7s8 3 8 7"
              stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>`;

    const aiIcon = `
      <svg viewBox="0 0 24 24" fill="none" class="role-icon">
        <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.5"/>
        <path d="M8 12h8M12 8v8"
              stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>`;

    const icon = role === "user" ? userIcon : aiIcon;

    // Preservar saltos de línea; el contenido ya está escapado
    const html = escapeHtml(content).replace(/\\n/g, "<br>");

    const div = document.createElement("div");
    div.className = `message message--${role}`;
    div.innerHTML = `
      <div class="message-bubble">
        <div class="message-content">${html}</div>
        <div class="message-time">${icon}${timeStr}</div>
      </div>`;
    return div;
  }

  // ── Eliminar el estado "conversación vacía" si existe ─────────────────────
  function removeEmptyState() {
    const empty = document.getElementById("emptyState");
    if (empty) empty.remove();
  }

  // ── Actualizar el título en el sidebar y en la cabecera del chat ──────────
  function updateTitle(newTitle) {
    const sidebarTitle = document.querySelector(
      ".conversation-item.active .conversation-title"
    );
    if (sidebarTitle) sidebarTitle.textContent = newTitle;

    const chatTitle = document.getElementById("chatTitle");
    if (chatTitle) chatTitle.textContent = newTitle;

    document.title = `${newTitle} — Azure AI Chat`;
  }

  // ── Bloquear / desbloquear la UI ───────────────────────────────────────────
  function setUILocked(locked) {
    sendButton.disabled = locked;
    input.disabled      = locked;
    if (!locked) input.focus();
  }

  // ── Envío del mensaje via AJAX ─────────────────────────────────────────────
  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    const content = input.value.trim();
    if (!content || !conversationId) return;

    setUILocked(true);
    input.value = "";
    autoResize();
    removeEmptyState();

    // Insertar burbuja del usuario de forma optimista
    const nowIso  = new Date().toISOString();
    const userEl  = buildMessageEl("user", content, formatTime(nowIso));
    messagesArea.insertBefore(userEl, typingIndicator);
    scrollToBottom(true);

    // Mostrar indicador de escritura
    typingIndicator.style.display = "block";
    scrollToBottom(true);

    try {
      const res = await fetch(
        `/api/conversations/${conversationId}/messages`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content }),
        }
      );

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Error HTTP ${res.status}`);
      }

      const data = await res.json();

      // Actualizar hora real del mensaje del usuario (la del servidor)
      if (data.user_message) {
        const timeEl = userEl.querySelector(".message-time");
        if (timeEl) {
          timeEl.innerHTML = timeEl.innerHTML.replace(
            /\\d{2}:\\d{2}/,
            formatTime(data.user_message.created_at)
          );
        }
      }

      // Ocultar indicador y mostrar respuesta del asistente
      typingIndicator.style.display = "none";
      const aiEl = buildMessageEl(
        "assistant",
        data.assistant_message.content,
        formatTime(data.assistant_message.created_at)
      );
      messagesArea.insertBefore(aiEl, typingIndicator);
      scrollToBottom(true);

      // Actualizar título si es el primer mensaje
      if (data.new_title) updateTitle(data.new_title);

    } catch (err) {
      typingIndicator.style.display = "none";

      // Mostrar el error en una burbuja roja
      const errEl = buildMessageEl(
        "assistant",
        `⚠️ ${err.message}`,
        formatTime(new Date().toISOString())
      );
      const bubble = errEl.querySelector(".message-bubble");
      if (bubble) {
        bubble.style.background    = "#fef2f2";
        bubble.style.borderColor   = "#fca5a5";
        bubble.style.border        = "1px solid #fca5a5";
      }
      const contentEl = errEl.querySelector(".message-content");
      if (contentEl) contentEl.style.color = "#dc2626";

      messagesArea.insertBefore(errEl, typingIndicator);
      scrollToBottom(true);
    } finally {
      setUILocked(false);
    }
  });

})();
"""

# ══════════════════════════════════════════════════════════════════════════════
#  ALEMBIC
# ══════════════════════════════════════════════════════════════════════════════

ALEMBIC_ENV = '''\
"""
alembic/env.py
==============
Configuración del entorno de migraciones Alembic.
Lee la URL de base de datos desde las variables de entorno del proyecto.
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Añadir la raíz del proyecto al path para poder importar app.*
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar Base y todos los modelos para que Alembic los detecte
from app.db.base import Base          # noqa: E402
import app.models                     # noqa: E402, F401  (registra modelos en metadata)

from app.core.config import settings  # noqa: E402

# Leer configuración de logging desde alembic.ini
alembic_cfg = context.config
if alembic_cfg.config_file_name is not None:
    fileConfig(alembic_cfg.config_file_name)

# Sobreescribir la URL con la del entorno
alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Modo offline: genera SQL sin conectar a la BD."""
    url = alembic_cfg.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Modo online: aplica migraciones conectando directamente a la BD."""
    connectable = engine_from_config(
        alembic_cfg.get_section(alembic_cfg.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''

ALEMBIC_MAKO = '''\
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
'''

MIGRATION_001 = '''\
"""Migración inicial: crea las tablas conversations y messages.

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Tabla conversations ──────────────────────────────────────────────────
    op.create_table(
        "conversations",
        sa.Column("id",         sa.Integer(),     nullable=False),
        sa.Column("title",      sa.String(255),   nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conversations_id", "conversations", ["id"], unique=False)

    # ── Tabla messages ───────────────────────────────────────────────────────
    op.create_table(
        "messages",
        sa.Column("id",              sa.Integer(),    nullable=False),
        sa.Column("conversation_id", sa.Integer(),    nullable=False),
        sa.Column("role",            sa.String(50),   nullable=False),
        sa.Column("content",         sa.Text(),       nullable=False),
        sa.Column("created_at",      sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_id",              "messages", ["id"],              unique=False)
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_index("ix_messages_id",              table_name="messages")
    op.drop_table("messages")
    op.drop_index("ix_conversations_id", table_name="conversations")
    op.drop_table("conversations")
'''

# ══════════════════════════════════════════════════════════════════════════════
#  README
# ══════════════════════════════════════════════════════════════════════════════

README = """\
# Azure AI Chat

Aplicación web de chat de IA conectada a **Azure OpenAI**, con historial de
conversaciones persistido en **PostgreSQL** (Azure).

---

## Stack tecnológico

| Capa            | Tecnología                                |
|-----------------|-------------------------------------------|
| Backend         | Python 3.11+ · FastAPI                    |
| Frontend        | Jinja2 · HTML5 · CSS3 · JavaScript Vanilla|
| Base de datos   | PostgreSQL (Azure Database for PostgreSQL)|
| ORM             | SQLAlchemy 2.x                            |
| Migraciones     | Alembic                                   |
| IA              | Azure OpenAI (SDK oficial `openai`)       |
| Configuración   | pydantic-settings + `.env`               |

---

## Arquitectura del proyecto

```
.
├── app/
│   ├── main.py               # Punto de entrada FastAPI
│   ├── core/
│   │   ├── config.py         # Variables de entorno (pydantic-settings)
│   │   └── logging_config.py # Configuración de logging
│   ├── db/
│   │   ├── base.py           # DeclarativeBase de SQLAlchemy
│   │   └── session.py        # Motor, SessionLocal y dependencia get_db
│   ├── models/
│   │   ├── conversation.py   # Modelo ORM → tabla conversations
│   │   └── message.py        # Modelo ORM → tabla messages
│   ├── schemas/
│   │   ├── conversation.py   # Schemas Pydantic para conversaciones
│   │   └── message.py        # Schemas Pydantic para mensajes
│   ├── services/
│   │   ├── conversation_service.py # Lógica de negocio: conversaciones
│   │   ├── message_service.py      # Lógica de negocio: mensajes
│   │   └── openai_service.py       # Cliente Azure OpenAI desacoplado
│   ├── routes/
│   │   ├── chat.py           # Rutas HTML (Jinja2)
│   │   └── api.py            # Rutas JSON (AJAX desde el frontend)
│   ├── templates/
│   │   ├── base.html         # Layout base con sidebar
│   │   ├── index.html        # Pantalla de bienvenida
│   │   └── conversation.html # Vista de chat
│   └── static/
│       ├── css/styles.css    # Hoja de estilos
│       └── js/chat.js        # Lógica del chat en el cliente
├── alembic/
│   ├── env.py                # Entorno Alembic
│   ├── script.py.mako        # Plantilla de revisiones
│   └── versions/
│       └── 001_initial_migration.py
├── alembic.ini
├── .env.example
├── requirements.txt
└── README.md
```

---

## Instalación y ejecución

### 1. Clonar / descargar el proyecto

```bash
git clone <url-del-repositorio>
cd ChatAzureOpenAIPostres_Entregable5
```

### 2. Crear y activar el entorno virtual

```bash
python -m venv venv

# Windows
venv\\Scripts\\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar las variables de entorno

```bash
cp .env.example .env
# Edita .env con tus credenciales reales
```

Variables obligatorias en `.env`:

| Variable                      | Descripción                                      |
|-------------------------------|--------------------------------------------------|
| `DATABASE_URL`                | URL de conexión a PostgreSQL                     |
| `AZURE_OPENAI_ENDPOINT`       | Endpoint del recurso Azure OpenAI                |
| `AZURE_OPENAI_API_KEY`        | Clave de API                                     |
| `AZURE_OPENAI_API_VERSION`    | Versión de la API (ej. `2024-02-15-preview`)     |
| `AZURE_OPENAI_DEPLOYMENT`     | Nombre del deployment (ej. `gpt-4`)              |

> **PostgreSQL en Azure:** La URL suele tener el formato
> `postgresql://usuario%40servidor:password@servidor.postgres.database.azure.com:5432/chatdb?sslmode=require`
> (el `@` del nombre de usuario se codifica como `%40`).

### 5. Ejecutar las migraciones

```bash
alembic upgrade head
```

### 6. Iniciar la aplicación

```bash
uvicorn app.main:app --reload
```

La aplicación queda disponible en **http://localhost:8000**.

---

## Endpoints

### Vistas HTML

| Método | Ruta                                     | Descripción                        |
|--------|------------------------------------------|------------------------------------|
| GET    | `/`                                      | Pantalla de bienvenida             |
| POST   | `/conversations/new`                     | Crear nueva conversación           |
| GET    | `/conversations/{id}`                    | Ver conversación                   |
| POST   | `/conversations/{id}/messages`           | Enviar mensaje (fallback sin JS)   |
| POST   | `/conversations/{id}/delete`             | Eliminar conversación              |

### API JSON

| Método | Ruta                                     | Descripción                        |
|--------|------------------------------------------|------------------------------------|
| GET    | `/api/conversations`                     | Listar conversaciones              |
| GET    | `/api/conversations/{id}`                | Obtener conversación con mensajes  |
| POST   | `/api/conversations/{id}/messages`       | Enviar mensaje (AJAX)              |

---

## Comandos Alembic

```bash
# Aplicar todas las migraciones pendientes
alembic upgrade head

# Crear una nueva migración (detecta cambios en los modelos)
alembic revision --autogenerate -m "descripcion_del_cambio"

# Revertir la última migración
alembic downgrade -1

# Ver el estado actual
alembic current

# Ver el historial de revisiones
alembic history
```

---

## Decisiones técnicas relevantes

- **Servicio OpenAI desacoplado** (`openai_service.py`): el cliente se inicializa
  de forma lazy para facilitar las pruebas sin conexión real.

- **Doble endpoint de mensajes**: la ruta `/conversations/{id}/messages` (POST form)
  actúa como fallback sin JavaScript; la ruta `/api/…` devuelve JSON y es la que
  usa el frontend por defecto.

- **Timestamp `updated_at`**: como SQLAlchemy no actualiza `onupdate` cuando se
  insertan filas hijas (mensajes), se llama explícitamente a `touch_conversation()`
  en cada envío para mantener el orden de la barra lateral.

- **XSS en el cliente**: el JS escapa el contenido de los mensajes antes de
  insertarlo en el DOM (`escapeHtml`).

- **Pool de conexiones**: configurado con `pool_pre_ping=True` para tolerar
  desconexiones de PostgreSQL en Azure (que pueden cerrar conexiones inactivas).
"""

# ══════════════════════════════════════════════════════════════════════════════
#  MAPA DE FICHEROS → contenido
# ══════════════════════════════════════════════════════════════════════════════

FILES = {
    # Configuración del proyecto
    "alembic.ini":                              ALEMBIC_INI,
    "README.md":                               README,

    # App
    "app/__init__.py":                          APP_INIT,
    "app/main.py":                              APP_MAIN,

    # Core
    "app/core/__init__.py":                     CORE_INIT,
    "app/core/config.py":                       CORE_CONFIG,
    "app/core/logging_config.py":               CORE_LOGGING,

    # DB
    "app/db/__init__.py":                       DB_INIT,
    "app/db/base.py":                           DB_BASE,
    "app/db/session.py":                        DB_SESSION,

    # Models
    "app/models/__init__.py":                   MODELS_INIT,
    "app/models/conversation.py":               MODELS_CONVERSATION,
    "app/models/message.py":                    MODELS_MESSAGE,

    # Schemas
    "app/schemas/__init__.py":                  SCHEMAS_INIT,
    "app/schemas/message.py":                   SCHEMAS_MESSAGE,
    "app/schemas/conversation.py":              SCHEMAS_CONVERSATION,

    # Services
    "app/services/__init__.py":                 SERVICES_INIT,
    "app/services/conversation_service.py":     SERVICES_CONVERSATION,
    "app/services/message_service.py":          SERVICES_MESSAGE,
    "app/services/openai_service.py":           SERVICES_OPENAI,

    # Routes
    "app/routes/__init__.py":                   ROUTES_INIT,
    "app/routes/chat.py":                       ROUTES_CHAT,
    "app/routes/api.py":                        ROUTES_API,

    # Templates
    "app/templates/base.html":                  TEMPLATE_BASE,
    "app/templates/index.html":                 TEMPLATE_INDEX,
    "app/templates/conversation.html":          TEMPLATE_CONVERSATION,

    # Static
    "app/static/css/styles.css":                STYLES_CSS,
    "app/static/js/chat.js":                    CHAT_JS,

    # Alembic
    "alembic/env.py":                           ALEMBIC_ENV,
    "alembic/script.py.mako":                   ALEMBIC_MAKO,
    "alembic/versions/001_initial_migration.py": MIGRATION_001,
}


# ══════════════════════════════════════════════════════════════════════════════
#  EJECUCIÓN
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    print(f"\\nGenerando proyecto en: {BASE}\\n")
    for rel_path, content in FILES.items():
        write(rel_path, content)
    print(f"\\n✅  {len(FILES)} ficheros creados correctamente.")
    print("\\nPróximos pasos:")
    print("  1. cp .env.example .env   (y edita las credenciales)")
    print("  2. pip install -r requirements.txt")
    print("  3. alembic upgrade head")
    print("  4. uvicorn app.main:app --reload")
    print()


if __name__ == "__main__":
    main()
