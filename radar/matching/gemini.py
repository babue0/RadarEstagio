import re

from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from radar.domain.models import Perfil, ResultadoMatch, Vaga
from radar.matching.avaliacoes import AvaliacoesIA, casar_avaliacoes_com_vagas
from radar.matching.errors import CotaDeAvaliacaoExcedida, ErroDeAvaliacao
from radar.matching.prompt import montar_prompt
from radar.settings import Settings

TEMPERATURA_DETERMINISTICA = 0
HTTP_COTA_EXCEDIDA = 429
PADRAO_TEMPO_DE_ESPERA = re.compile(r"retry in ([\d.]+)s", re.IGNORECASE)


class AvaliadorGemini:
    def __init__(self, settings: Settings, cliente: genai.Client) -> None:
        self._modelo = settings.gemini_modelo
        self._cliente = cliente

    def avaliar(self, vagas: list[Vaga], perfil: Perfil) -> list[ResultadoMatch]:
        if not vagas:
            return []
        avaliacoes = self._pedir_avaliacoes(montar_prompt(vagas, perfil))
        return casar_avaliacoes_com_vagas(avaliacoes, vagas, perfil)

    def _pedir_avaliacoes(self, prompt: str) -> AvaliacoesIA:
        try:
            resposta = self._cliente.models.generate_content(
                model=self._modelo,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AvaliacoesIA,
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


def interpretar_resposta(texto: str | None) -> AvaliacoesIA:
    if not texto:
        raise ErroDeAvaliacao("Gemini devolveu resposta vazia")
    try:
        return AvaliacoesIA.model_validate_json(texto)
    except ValidationError as erro:
        raise ErroDeAvaliacao(f"Gemini devolveu JSON fora do esperado: {erro}") from None
