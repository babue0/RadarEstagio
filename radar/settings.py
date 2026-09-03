from typing import Literal, Self

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

FONTES_DISPONIVEIS = ("adzuna", "gupy")
SEPARADOR_DE_FONTES = ","


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
    telegram_chat_id: str = ""
    database_url: str = ""
    fontes: str = SEPARADOR_DE_FONTES.join(FONTES_DISPONIVEIS)
    dias_recentes: int = Field(default=3, ge=1)
    quantidade_vagas_enviadas: int = 5
    nota_minima: int = Field(default=40, ge=0, le=100)
    falhas_de_envio_ate_pausar: int = Field(default=3, ge=1)

    @field_validator("fontes")
    @classmethod
    def exigir_fontes_conhecidas(cls, valor: str) -> str:
        nomes = separar_fontes(valor)
        desconhecidas = [nome for nome in nomes if nome not in FONTES_DISPONIVEIS]
        if not nomes or desconhecidas:
            raise ValueError(
                f"FONTES deve listar ao menos uma entre {', '.join(FONTES_DISPONIVEIS)}"
            )
        return valor

    def fontes_selecionadas(self) -> list[str]:
        return separar_fontes(self.fontes)

    def usa_banco(self) -> bool:
        return bool(self.database_url.strip())

    @model_validator(mode="after")
    def exigir_chave_no_modo_gemini_api(self) -> Self:
        if self.avaliador == "gemini_api" and not self.gemini_api_key.strip():
            raise ValueError("GEMINI_API_KEY é obrigatória quando AVALIADOR=gemini_api")
        return self

    @model_validator(mode="after")
    def exigir_chat_id_sem_banco(self) -> Self:
        if not self.usa_banco() and not self.telegram_chat_id.strip():
            raise ValueError("TELEGRAM_CHAT_ID é obrigatório quando DATABASE_URL está vazio")
        return self


def separar_fontes(valor: str) -> list[str]:
    return [nome.strip().lower() for nome in valor.split(SEPARADOR_DE_FONTES) if nome.strip()]
