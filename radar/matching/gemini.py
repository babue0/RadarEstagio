import re

from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from radar.domain.models import ExtracaoDaVaga, Vaga
from radar.matching.errors import CotaDeAvaliacaoExcedida, ErroDeAvaliacao
from radar.matching.extracao import ExtracoesDeVagas
from radar.matching.prompt import montar_prompt
from radar.settings import Settings

TEMPERATURA_DETERMINISTICA = 0
HTTP_COTA_EXCEDIDA = 429
PADRAO_TEMPO_DE_ESPERA = re.compile(r"retry in ([\d.]+)s", re.IGNORECASE)


class ExtratorGemini:
    def __init__(self, settings: Settings, cliente: genai.Client) -> None:
        self._modelo = settings.gemini_modelo
        self._cliente = cliente

    def extrair(self, vagas: list[Vaga]) -> list[ExtracaoDaVaga]:
        if not vagas:
            return []
        return self._pedir_extracoes(montar_prompt(vagas)).extracoes

    def _pedir_extracoes(self, prompt: str) -> ExtracoesDeVagas:
        try:
            resposta = self._cliente.models.generate_content(
                model=self._modelo,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ExtracoesDeVagas,
                    temperature=TEMPERATURA_DETERMINISTICA,
                ),
            )
        except errors.APIError as erro:
            mensagem = f"Gemini respondeu HTTP {erro.code}: {erro.message}"
            if erro.code == HTTP_COTA_EXCEDIDA:
                raise CotaDeAvaliacaoExcedida(mensagem, tempo_de_espera(erro.message)) from None
            raise ErroDeAvaliacao(mensagem) from None
        return interpretar_resposta(resposta.text)


def tempo_de_espera(mensagem: str | None) -> float | None:
    encontrado = PADRAO_TEMPO_DE_ESPERA.search(mensagem or "")
    return float(encontrado.group(1)) if encontrado else None


def interpretar_resposta(texto: str | None) -> ExtracoesDeVagas:
    if not texto:
        raise ErroDeAvaliacao("Gemini devolveu resposta vazia")
    try:
        return ExtracoesDeVagas.model_validate_json(texto)
    except ValidationError as erro:
        raise ErroDeAvaliacao(f"Gemini devolveu JSON fora do esperado: {erro}") from None
