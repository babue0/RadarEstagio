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
    id_vaga: str
    nota: int = Field(ge=0, le=100)
    motivo: str
    alerta_pegadinha: str | None = None


class AvaliacoesIA(BaseModel):
    avaliacoes: list[AvaliacaoIA]


class AvaliadorGemini:
    def __init__(self, settings: Settings, cliente: genai.Client) -> None:
        self._modelo = settings.gemini_modelo
        self._cliente = cliente

    def avaliar(self, vagas: list[Vaga], perfil: Perfil) -> list[ResultadoMatch]:
        if not vagas:
            return []
        avaliacoes = self._pedir_avaliacoes(montar_prompt(vagas, perfil))
        return casar_avaliacoes_com_vagas(avaliacoes, vagas)

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
                raise CotaDeAvaliacaoExcedida(mensagem) from None
            raise ErroDeAvaliacao(mensagem) from None
        return interpretar_resposta(resposta.text)


def interpretar_resposta(texto: str | None) -> AvaliacoesIA:
    if not texto:
        raise ErroDeAvaliacao("Gemini devolveu resposta vazia")
    try:
        return AvaliacoesIA.model_validate_json(texto)
    except ValidationError as erro:
        raise ErroDeAvaliacao(f"Gemini devolveu JSON fora do esperado: {erro}") from None


def casar_avaliacoes_com_vagas(avaliacoes: AvaliacoesIA, vagas: list[Vaga]) -> list[ResultadoMatch]:
    vagas_por_id = {vaga.id_externo: vaga for vaga in vagas}
    resultados: dict[str, ResultadoMatch] = {}
    for avaliacao in avaliacoes.avaliacoes:
        vaga = vagas_por_id.get(avaliacao.id_vaga)
        if vaga is None or avaliacao.id_vaga in resultados:
            continue
        resultados[avaliacao.id_vaga] = ResultadoMatch(
            vaga=vaga,
            nota=avaliacao.nota,
            motivo=avaliacao.motivo,
            alerta_pegadinha=avaliacao.alerta_pegadinha,
        )
    return list(resultados.values())
