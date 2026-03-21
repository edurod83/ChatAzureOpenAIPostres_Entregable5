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
