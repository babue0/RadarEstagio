from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    adzuna_app_id: str = Field(min_length=1)
    adzuna_app_key: str = Field(min_length=1)
    avaliador: Literal["gemini_api", "agy"] = "gemini_api"
    gemini_api_key: str = ""
    gemini_modelo: str = "gemini-3.6-flash"
    gemini_vagas_por_lote: int = Field(default=10, ge=1)
    agy_modelo: str = "gemini-3.6-flash-low"
    agy_timeout_segundos: int = Field(default=300, ge=1)
    telegram_bot_token: str = Field(min_length=1)
    telegram_chat_id: str = Field(min_length=1)
    adzuna_dias_recentes: int = 2
    quantidade_vagas_enviadas: int = 5

    @model_validator(mode="after")
    def exigir_chave_no_modo_gemini_api(self) -> Self:
        if self.avaliador == "gemini_api" and not self.gemini_api_key.strip():
            raise ValueError("GEMINI_API_KEY é obrigatória quando AVALIADOR=gemini_api")
        return self
