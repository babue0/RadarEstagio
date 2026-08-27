from datetime import datetime, timedelta

import httpx

from radar.collectors.adzuna import ColetorAdzuna
from radar.collectors.composto import ColetorComposto
from radar.collectors.gupy import ColetorGupy
from radar.domain.ports import ColetorDeVagas
from radar.settings import Settings


def criar_coletor(
    settings: Settings, cliente_http: httpx.Client, agora: datetime
) -> ColetorDeVagas:
    publicadas_desde = agora - timedelta(days=settings.dias_recentes)
    coletores_disponiveis: dict[str, ColetorDeVagas] = {
        "adzuna": ColetorAdzuna(settings, cliente_http),
        "gupy": ColetorGupy(cliente_http, publicadas_desde),
    }
    return ColetorComposto(
        {fonte: coletores_disponiveis[fonte] for fonte in settings.fontes_selecionadas()}
    )
