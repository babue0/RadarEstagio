from collections.abc import Iterable
from datetime import datetime, timedelta

import httpx

from radar.collectors.adzuna import ColetorAdzuna
from radar.collectors.composto import ColetorComposto
from radar.collectors.gupy import ColetorGupy
from radar.domain.models import Modalidade, Usuario
from radar.domain.ports import ColetorDeVagas
from radar.settings import Settings

MODALIDADES_QUE_DEPENDEM_DA_CIDADE = frozenset({Modalidade.PRESENCIAL, Modalidade.HIBRIDO})


def criar_coletor(
    settings: Settings,
    cliente_http: httpx.Client,
    agora: datetime,
    cidades: Iterable[str] = (),
) -> ColetorDeVagas:
    publicadas_desde = agora - timedelta(days=settings.dias_recentes)
    cidades_de_busca = tuple(cidades)
    coletores_disponiveis: dict[str, ColetorDeVagas] = {
        "adzuna": ColetorAdzuna(settings, cliente_http, cidades_de_busca),
        "gupy": ColetorGupy(cliente_http, publicadas_desde, cidades_de_busca),
    }
    return ColetorComposto(
        {fonte: coletores_disponiveis[fonte] for fonte in settings.fontes_selecionadas()}
    )


def cidades_de_interesse(usuarios: Iterable[Usuario]) -> list[str]:
    cidades = {
        usuario.perfil.nome_da_cidade()
        for usuario in usuarios
        if usuario.perfil.modalidade in MODALIDADES_QUE_DEPENDEM_DA_CIDADE
    }
    return sorted(cidades)
