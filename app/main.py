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
    # Crear tablas si no existen (equivalente a alembic upgrade head para tablas nuevas)
    from app.db.base import Base
    from app.db.session import engine
    import app.models.conversation  # noqa: F401 — registra el modelo en Base
    import app.models.message       # noqa: F401 — registra el modelo en Base
    Base.metadata.create_all(bind=engine)
    logger.info("Tablas verificadas/creadas.")
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
