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
