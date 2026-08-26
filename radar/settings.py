from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    adzuna_app_id: str = Field(min_length=1)
    adzuna_app_key: str = Field(min_length=1)
    gemini_api_key: str = Field(min_length=1)
    gemini_modelo: str = "gemini-3.6-flash"
    gemini_vagas_por_lote: int = Field(default=10, ge=1)
    telegram_bot_token: str = Field(min_length=1)
    telegram_chat_id: str = Field(min_length=1)
    adzuna_dias_recentes: int = 2
    quantidade_vagas_enviadas: int = 5
