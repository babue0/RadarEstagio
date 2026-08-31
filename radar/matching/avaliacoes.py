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
PESO_OBRIGATORIAS_COM_PRINCIPAIS = 0.7
PESO_PRINCIPAIS_COM_OBRIGATORIAS = 0.3
PESO_PRINCIPAIS_COM_DESEJAVEIS = 0.8
PESO_DESEJAVEIS_COM_PRINCIPAIS = 0.2
PESO_OBRIGATORIAS_QUANDO_TODAS = 0.6
PESO_PRINCIPAIS_QUANDO_TODAS = 0.3
PESO_DESEJAVEIS_QUANDO_TODAS = 0.1
COBERTURA_NEUTRA_SEM_STACK_DECLARADA = 0.5
LIMITE_COM_HABILIDADE_OBRIGATORIA_AUSENTE = 60
LIMITE_COM_MAIORIA_DAS_HABILIDADES_PRINCIPAIS_AUSENTE = 70
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
    habilidades_principais: list[str] = Field(default_factory=list)
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
        requisitos_atendidos, requisitos_nao_atendidos = _classificar_habilidades(
            avaliacao, perfil
        )
        requisitos = _juntar_habilidades_da_vaga(avaliacao)
        resultados[avaliacao.id_vaga] = ResultadoMatch(
            vaga=vaga,
            nota=_calcular_nota(avaliacao, vaga, perfil),
            requisitos_atendidos=requisitos_atendidos,
            requisitos_nao_atendidos=requisitos_nao_atendidos,
            requisitos_tecnicos_analisados=True,
            pontos_a_favor=_juntar_sem_repetir(
                _remover_explicacoes_de_habilidades(avaliacao.pontos_a_favor, requisitos)
            ),
            pontos_contra=_juntar_sem_repetir(
                _remover_explicacoes_de_habilidades(avaliacao.pontos_contra, requisitos)
            ),
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
    nota_arredondada = int(nota + 0.5)
    return min(nota_arredondada, _limite_por_habilidades(avaliacao, perfil))


def _limite_por_habilidades(avaliacao: AvaliacaoIA, perfil: Perfil) -> int:
    cobertura_obrigatorias = _cobertura(
        avaliacao.habilidades_obrigatorias, perfil.habilidades
    )
    if cobertura_obrigatorias is not None and cobertura_obrigatorias < 1:
        return LIMITE_COM_HABILIDADE_OBRIGATORIA_AUSENTE
    cobertura_principais = _cobertura(avaliacao.habilidades_principais, perfil.habilidades)
    if cobertura_principais is not None and cobertura_principais < 0.5:
        return LIMITE_COM_MAIORIA_DAS_HABILIDADES_PRINCIPAIS_AUSENTE
    return 100


def _compatibilidade_de_habilidades(avaliacao: AvaliacaoIA, perfil: Perfil) -> float:
    obrigatorias = _cobertura(avaliacao.habilidades_obrigatorias, perfil.habilidades)
    principais = _cobertura(avaliacao.habilidades_principais, perfil.habilidades)
    desejaveis = _cobertura(avaliacao.habilidades_desejaveis, perfil.habilidades)
    if obrigatorias is not None and principais is not None and desejaveis is not None:
        return (
            PESO_OBRIGATORIAS_QUANDO_TODAS * obrigatorias
            + PESO_PRINCIPAIS_QUANDO_TODAS * principais
            + PESO_DESEJAVEIS_QUANDO_TODAS * desejaveis
        )
    if obrigatorias is not None and principais is not None:
        return (
            PESO_OBRIGATORIAS_COM_PRINCIPAIS * obrigatorias
            + PESO_PRINCIPAIS_COM_OBRIGATORIAS * principais
        )
    if obrigatorias is not None and desejaveis is not None:
        return (
            PESO_OBRIGATORIAS_QUANDO_MISTAS * obrigatorias
            + PESO_DESEJAVEIS_QUANDO_MISTAS * desejaveis
        )
    if principais is not None and desejaveis is not None:
        return (
            PESO_PRINCIPAIS_COM_DESEJAVEIS * principais
            + PESO_DESEJAVEIS_COM_PRINCIPAIS * desejaveis
        )
    if obrigatorias is not None:
        return obrigatorias
    if principais is not None:
        return principais
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


def _classificar_habilidades(
    avaliacao: AvaliacaoIA, perfil: Perfil
) -> tuple[list[str], list[str]]:
    habilidades_do_perfil = {
        _normalizar_habilidade(item) for item in perfil.habilidades if item.strip()
    }
    requisitos = _juntar_habilidades_da_vaga(avaliacao)
    requisitos_atendidos = [
        habilidade
        for habilidade in requisitos
        if _normalizar_habilidade(habilidade) in habilidades_do_perfil
    ]
    requisitos_nao_atendidos = [
        habilidade
        for habilidade in requisitos
        if _normalizar_habilidade(habilidade) not in habilidades_do_perfil
    ]
    return requisitos_atendidos, requisitos_nao_atendidos


def _juntar_habilidades_da_vaga(avaliacao: AvaliacaoIA) -> list[str]:
    habilidades = (
        avaliacao.habilidades_obrigatorias
        + avaliacao.habilidades_principais
        + avaliacao.habilidades_desejaveis
    )
    unicas: dict[str, str] = {}
    for habilidade in habilidades:
        if habilidade.strip():
            unicas.setdefault(_normalizar_habilidade(habilidade), habilidade.strip())
    return list(unicas.values())


def _juntar_sem_repetir(*grupos: list[str]) -> list[str]:
    unicos: dict[str, str] = {}
    for item in (item for grupo in grupos for item in grupo):
        if item.strip():
            unicos.setdefault(_normalizar_texto(item), item.strip())
    return list(unicos.values())


def _remover_explicacoes_de_habilidades(
    pontos: list[str], habilidades: list[str]
) -> list[str]:
    rotulos_de_habilidades = {
        _normalizar_texto(rotulo)
        for habilidade in habilidades
        for rotulo in (
            habilidade,
            f"{habilidade} informado",
            f"{habilidade} não informado",
        )
    }
    return [ponto for ponto in pontos if _normalizar_texto(ponto) not in rotulos_de_habilidades]


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
