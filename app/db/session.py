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
