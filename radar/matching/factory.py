from google import genai

from radar.domain.ports import AvaliadorDeVagas
from radar.matching.agy import AvaliadorAgy
from radar.matching.gemini import AvaliadorGemini
from radar.settings import Settings


def criar_avaliador(settings: Settings) -> AvaliadorDeVagas:
    if settings.avaliador == "agy":
        return AvaliadorAgy(settings)
    cliente = genai.Client(api_key=settings.gemini_api_key)
    return AvaliadorGemini(settings, cliente)


def nome_do_modelo(settings: Settings) -> str:
    if settings.avaliador == "agy":
        return settings.agy_modelo
    return settings.gemini_modelo
