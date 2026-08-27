import pytest
from pydantic import ValidationError

from radar.settings import Settings


def configuracao_base(**sobrescritas: str) -> dict[str, str]:
    valores = {
        "adzuna_app_id": "adzuna-id",
        "adzuna_app_key": "adzuna-chave",
        "gemini_api_key": "",
        "telegram_bot_token": "telegram-token",
        "telegram_chat_id": "123",
    }
    valores.update(sobrescritas)
    return valores


def test_modo_agy_nao_exige_chave_da_api_gemini():
    settings = Settings(_env_file=None, **configuracao_base(avaliador="agy"))

    assert settings.avaliador == "agy"
    assert settings.gemini_api_key == ""


def test_modo_gemini_api_exige_chave():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **configuracao_base(avaliador="gemini_api"))
