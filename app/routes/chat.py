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
        title = content[:60] + ("…" if len(content) > 60 else "")
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
