from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field, ValidationError

from radar.domain.models import Perfil, ResultadoMatch, Vaga
from radar.matching.prompt import montar_prompt
from radar.settings import Settings

TEMPERATURA_DETERMINISTICA = 0
HTTP_COTA_EXCEDIDA = 429


class ErroDeAvaliacao(Exception):
    pass


class CotaDeAvaliacaoExcedida(ErroDeAvaliacao):
    pass


class AvaliacaoIA(BaseModel):
    nota: int = Field(ge=0, le=100)
    motivo: str
    alerta_pegadinha: str | None = None


class AvaliadorGemini:
    def __init__(self, settings: Settings, cliente: genai.Client) -> None:
        self._modelo = settings.gemini_modelo
        self._cliente = cliente

    def avaliar(self, vaga: Vaga, perfil: Perfil) -> ResultadoMatch:
        avaliacao = self._pedir_avaliacao(montar_prompt(vaga, perfil))
        return ResultadoMatch(
            vaga=vaga,
            nota=avaliacao.nota,
            motivo=avaliacao.motivo,
            alerta_pegadinha=avaliacao.alerta_pegadinha,
        )

    def _pedir_avaliacao(self, prompt: str) -> AvaliacaoIA:
        try:
            resposta = self._cliente.models.generate_content(
                model=self._modelo,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AvaliacaoIA,
                    temperature=TEMPERATURA_DETERMINISTICA,
                ),
            )
        except errors.APIError as erro:
            mensagem = f"Gemini respondeu HTTP {erro.code}: {erro.message}"
            if erro.code == HTTP_COTA_EXCEDIDA:
                raise CotaDeAvaliacaoExcedida(mensagem) from None
            raise ErroDeAvaliacao(mensagem) from None
        return interpretar_resposta(resposta.text)


def interpretar_resposta(texto: str | None) -> AvaliacaoIA:
    if not texto:
        raise ErroDeAvaliacao("Gemini devolveu resposta vazia")
    try:
        return AvaliacaoIA.model_validate_json(texto)
    except ValidationError as erro:
        raise ErroDeAvaliacao(f"Gemini devolveu JSON fora do esperado: {erro}") from None
