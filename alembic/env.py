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
