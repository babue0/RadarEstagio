from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    adzuna_app_id: str
    adzuna_app_key: str
    gemini_api_key: str
    telegram_bot_token: str
    telegram_chat_id: str
    adzuna_dias_recentes: int = 2
    quantidade_vagas_enviadas: int = 5
