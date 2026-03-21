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
                max_completion_tokens=2000,
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
