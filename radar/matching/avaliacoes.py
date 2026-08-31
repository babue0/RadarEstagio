import unicodedata
from enum import StrEnum

from pydantic import BaseModel, Field

from radar.domain.models import Modalidade, Perfil, ResultadoMatch, Vaga

PESO_HABILIDADES = 50
PESO_CURSO = 15
PESO_AREA = 10
PESO_PERIODO_EXPERIENCIA = 15
PESO_LOGISTICA = 10
PESO_OBRIGATORIAS_QUANDO_MISTAS = 0.8
PESO_DESEJAVEIS_QUANDO_MISTAS = 0.2
COBERTURA_NEUTRA_SEM_STACK_DECLARADA = 0.5
COEFICIENTES = {
    "compativel": 1.0,
    "parcial": 0.5,
    "incompativel": 0.0,
}
ALIASES_DE_HABILIDADES = {
    "cplusplus": "c++",
    "cpp": "c++",
    "csharp": "c#",
    "css3": "css",
    "golang": "go",
    "html5": "html",
    "js": "javascript",
    "node": "nodejs",
    "postgres": "postgresql",
    "python3": "python",
    "reactjs": "react",
    "restapi": "rest",
    "ts": "typescript",
    "vuejs": "vue",
}


class NivelCompatibilidade(StrEnum):
    COMPATIVEL = "compativel"
    PARCIAL = "parcial"
    INCOMPATIVEL = "incompativel"


class AvaliacaoIA(BaseModel):
    id_vaga: str
    area: NivelCompatibilidade
    curso: NivelCompatibilidade
    periodo_experiencia: NivelCompatibilidade
    habilidades_obrigatorias: list[str] = Field(default_factory=list)
    habilidades_desejaveis: list[str] = Field(default_factory=list)
    pontos_a_favor: list[str] = Field(default_factory=list)
    pontos_contra: list[str] = Field(default_factory=list)
    alerta_pegadinha: str | None = None


class AvaliacoesIA(BaseModel):
    avaliacoes: list[AvaliacaoIA]


def casar_avaliacoes_com_vagas(
    avaliacoes: AvaliacoesIA, vagas: list[Vaga], perfil: Perfil
) -> list[ResultadoMatch]:
    vagas_por_id = {vaga.id_externo: vaga for vaga in vagas}
    resultados: dict[str, ResultadoMatch] = {}
    for avaliacao in avaliacoes.avaliacoes:
        vaga = vagas_por_id.get(avaliacao.id_vaga)
        if vaga is None or avaliacao.id_vaga in resultados:
            continue
        resultados[avaliacao.id_vaga] = ResultadoMatch(
            vaga=vaga,
            nota=_calcular_nota(avaliacao, vaga, perfil),
            pontos_a_favor=avaliacao.pontos_a_favor,
            pontos_contra=avaliacao.pontos_contra,
            alerta_pegadinha=avaliacao.alerta_pegadinha,
        )
    return list(resultados.values())


def _calcular_nota(avaliacao: AvaliacaoIA, vaga: Vaga, perfil: Perfil) -> int:
    nota = (
        PESO_HABILIDADES * _compatibilidade_de_habilidades(avaliacao, perfil)
        + PESO_CURSO * _coeficiente(avaliacao.curso)
        + PESO_AREA * _coeficiente(avaliacao.area)
        + PESO_PERIODO_EXPERIENCIA * _coeficiente(avaliacao.periodo_experiencia)
        + PESO_LOGISTICA * _compatibilidade_logistica(vaga, perfil)
    )
    return int(nota + 0.5)


def _compatibilidade_de_habilidades(avaliacao: AvaliacaoIA, perfil: Perfil) -> float:
    obrigatorias = _cobertura(avaliacao.habilidades_obrigatorias, perfil.habilidades)
    desejaveis = _cobertura(avaliacao.habilidades_desejaveis, perfil.habilidades)
    if obrigatorias is not None and desejaveis is not None:
        return (
            PESO_OBRIGATORIAS_QUANDO_MISTAS * obrigatorias
            + PESO_DESEJAVEIS_QUANDO_MISTAS * desejaveis
        )
    if obrigatorias is not None:
        return obrigatorias
    if desejaveis is not None:
        return desejaveis
    return COBERTURA_NEUTRA_SEM_STACK_DECLARADA


def _cobertura(requisitos: list[str], habilidades: list[str]) -> float | None:
    requisitos_normalizados = {_normalizar_habilidade(item) for item in requisitos if item.strip()}
    if not requisitos_normalizados:
        return None
    habilidades_normalizadas = {
        _normalizar_habilidade(item) for item in habilidades if item.strip()
    }
    atendidas = requisitos_normalizados & habilidades_normalizadas
    return len(atendidas) / len(requisitos_normalizados)


def _normalizar_habilidade(habilidade: str) -> str:
    normalizada = _normalizar_texto(habilidade)
    compacta = "".join(
        caractere for caractere in normalizada if caractere.isalnum() or caractere in "#+"
    )
    return ALIASES_DE_HABILIDADES.get(compacta, compacta)


def _coeficiente(nivel: NivelCompatibilidade) -> float:
    return COEFICIENTES[nivel.value]


def _compatibilidade_logistica(vaga: Vaga, perfil: Perfil) -> float:
    localizacao = _compatibilidade_de_localizacao(vaga, perfil)
    modalidade = _compatibilidade_de_modalidade(vaga, perfil)
    return (localizacao + modalidade) / 2


def _compatibilidade_de_localizacao(vaga: Vaga, perfil: Perfil) -> float:
    if vaga.modalidade is Modalidade.REMOTO or perfil.modalidade is Modalidade.REMOTO:
        return 1.0
    cidade_da_vaga = _normalizar_texto(vaga.localizacao.split(",")[0])
    cidade_do_perfil = _normalizar_texto(perfil.nome_da_cidade())
    return 1.0 if cidade_da_vaga == cidade_do_perfil else 0.0


def _compatibilidade_de_modalidade(vaga: Vaga, perfil: Perfil) -> float:
    if vaga.modalidade is None:
        return 0.5
    if perfil.modalidade is Modalidade.INDIFERENTE or vaga.modalidade is perfil.modalidade:
        return 1.0
    if perfil.modalidade is Modalidade.PRESENCIAL and vaga.modalidade is Modalidade.HIBRIDO:
        return 0.5
    return 0.0


def _normalizar_texto(texto: str) -> str:
    sem_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return sem_acentos.casefold().strip()
