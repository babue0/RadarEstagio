from radar.matching.agy import ExtratorAgy
from radar.matching.factory import criar_extrator
from radar.matching.gemini import ExtratorGemini
from radar.settings import Settings


def test_cria_extrator_agy_quando_selecionado():
    settings = Settings(
        _env_file=None,
        adzuna_app_id="adzuna-id",
        adzuna_app_key="adzuna-chave",
        avaliador="agy",
        gemini_api_key="",
        telegram_bot_token="telegram-token",
        telegram_chat_id="123",
    )

    assert isinstance(criar_extrator(settings), ExtratorAgy)


def test_preserva_extrator_gemini_api_quando_selecionado():
    settings = Settings(
        _env_file=None,
        adzuna_app_id="adzuna-id",
        adzuna_app_key="adzuna-chave",
        avaliador="gemini_api",
        gemini_api_key="gemini-chave",
        telegram_bot_token="telegram-token",
        telegram_chat_id="123",
    )

    assert isinstance(criar_extrator(settings), ExtratorGemini)
