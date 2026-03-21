"""
app/core/config.py
==================
Configuración centralizada de la aplicación.
Todas las variables se leen desde el fichero .env o variables de entorno.
"""

from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
    SecretsSettingsSource,
)


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

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        **kwargs: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # El .env tiene prioridad sobre las variables de entorno del sistema
        return (
            kwargs["init_settings"],
            kwargs["dotenv_settings"],
            kwargs["env_settings"],
        )


# Instancia global; importar desde aquí en el resto de módulos
settings = Settings()
