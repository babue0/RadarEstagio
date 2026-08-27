from pydantic import BaseModel, Field

from radar.domain.models import ResultadoMatch, Vaga


class AvaliacaoIA(BaseModel):
    id_vaga: str
    nota: int = Field(ge=0, le=100)
    pontos_a_favor: list[str] = Field(default_factory=list)
    pontos_contra: list[str] = Field(default_factory=list)
    alerta_pegadinha: str | None = None


class AvaliacoesIA(BaseModel):
    avaliacoes: list[AvaliacaoIA]


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
            pontos_a_favor=avaliacao.pontos_a_favor,
            pontos_contra=avaliacao.pontos_contra,
            alerta_pegadinha=avaliacao.alerta_pegadinha,
        )
    return list(resultados.values())
