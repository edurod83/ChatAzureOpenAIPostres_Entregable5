"""
app/services/openai_service.py
==============================
Servicio de chat basado en LangChain + Azure OpenAI.
Usa AzureChatOpenAI de langchain-openai y gestiona el historial
mediante ChatPromptTemplate con soporte de memoria de conversación.
"""

import logging
from typing import Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import AzureChatOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class LangChainChatService:
    """
    Servicio de chat que utiliza LangChain como framework principal.
    Construye una cadena simple: prompt | llm y gestiona el historial
    de mensajes en formato LangChain antes de enviarlos al modelo.
    """

    def __init__(self) -> None:
        self._llm: Optional[AzureChatOpenAI] = None
        self.system_prompt = settings.SYSTEM_PROMPT

    @property
    def llm(self) -> AzureChatOpenAI:
        """Inicialización lazy del LLM para facilitar las pruebas."""
        if self._llm is None:
            self._llm = AzureChatOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
                max_tokens=2000,
                timeout=60,
            )
        return self._llm

    def _build_chain(self):
        """Construye la cadena LangChain: prompt | llm."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="history"),
        ])
        return prompt | self.llm

    def _to_langchain_messages(self, messages: List[Dict[str, str]]):
        """Convierte el historial de dicts a objetos de mensaje LangChain."""
        result = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                result.append(HumanMessage(content=content))
            elif role == "assistant":
                result.append(AIMessage(content=content))
            elif role == "system":
                result.append(SystemMessage(content=content))
        return result

    def chat_completion(self, messages: List[Dict[str, str]]) -> str:
        """
        Envía el historial al modelo vía LangChain y devuelve la respuesta.

        Args:
            messages: Lista de dicts con 'role' y 'content' (formato OpenAI).

        Returns:
            Texto de respuesta del asistente.

        Raises:
            RuntimeError: Si ocurre un error irrecuperable.
        """
        history = self._to_langchain_messages(messages)

        logger.info(
            "LangChain → Azure OpenAI: deployment=%s, mensajes=%d",
            settings.AZURE_OPENAI_DEPLOYMENT,
            len(history),
        )

        try:
            chain = self._build_chain()
            response = chain.invoke({"history": history})
            content = response.content or ""
            logger.info("Respuesta recibida: %d caracteres", len(content))
            return content

        except Exception as e:
            error_msg = str(e).lower()
            logger.error("Error LangChain/Azure OpenAI: %s", e)

            if "connection" in error_msg or "network" in error_msg:
                raise RuntimeError(
                    "No se pudo conectar con el servicio de IA. "
                    "Verifica el endpoint y la clave de API."
                ) from e
            if "timeout" in error_msg:
                raise RuntimeError(
                    "El servicio de IA tardó demasiado en responder. "
                    "Inténtalo de nuevo."
                ) from e
            raise RuntimeError(
                "Error del servicio de IA. Inténtalo de nuevo."
            ) from e


# Instancia singleton — compatible con el nombre esperado por las rutas
openai_service = LangChainChatService()
