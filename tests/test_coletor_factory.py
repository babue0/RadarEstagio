import re
from datetime import UTC, datetime
from uuid import UUID

import httpx
from pytest_httpx import HTTPXMock

from radar.collectors.adzuna import URL_BUSCA as URL_ADZUNA
from radar.collectors.factory import cidades_de_interesse, criar_coletor
from radar.collectors.gupy import URL_BUSCA as URL_GUPY
from radar.domain.models import Modalidade, Perfil, Usuario
from radar.settings import Settings

AGORA = datetime(2026, 8, 27, 12, 0, tzinfo=UTC)


def usuario(numero: int, cidade: str, modalidade: Modalidade) -> Usuario:
    perfil = Perfil(
        curso="Ciência da Computação",
        periodo=3,
        habilidades=["Python"],
        cidade=cidade,
        modalidade=modalidade,
    )
    return Usuario(id=UUID(int=numero), perfil=perfil, chat_id=str(numero))


def settings_de_teste(fontes: str) -> Settings:
    return Settings(
        _env_file=None,
        adzuna_app_id="adzuna-id",
        adzuna_app_key="adzuna-chave",
        gemini_api_key="gemini-chave",
        telegram_bot_token="telegram-token",
        telegram_chat_id="123",
        fontes=fontes,
    )


def hosts_consultados(httpx_mock: HTTPXMock) -> set[str]:
    return {requisicao.url.host for requisicao in httpx_mock.get_requests()}


def test_consulta_somente_as_fontes_selecionadas(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=re.compile(re.escape(URL_ADZUNA)), json={"results": []})
    with httpx.Client() as cliente_http:
        criar_coletor(settings_de_teste("adzuna"), cliente_http, AGORA).coletar()

    assert hosts_consultados(httpx_mock) == {httpx.URL(URL_ADZUNA).host}


def test_consulta_todas_as_fontes_por_padrao(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=re.compile(re.escape(URL_ADZUNA)), json={"results": []})
    httpx_mock.add_response(
        url=re.compile(re.escape(URL_GUPY)), json={"data": []}, is_reusable=True
    )
    with httpx.Client() as cliente_http:
        criar_coletor(settings_de_teste("adzuna, gupy"), cliente_http, AGORA).coletar()

    assert hosts_consultados(httpx_mock) == {httpx.URL(URL_ADZUNA).host, httpx.URL(URL_GUPY).host}


def test_repassa_cidades_para_todas_as_fontes(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=re.compile(re.escape(URL_ADZUNA)), json={"results": []}, is_reusable=True
    )
    httpx_mock.add_response(
        url=re.compile(re.escape(URL_GUPY)), json={"data": []}, is_reusable=True
    )
    with httpx.Client() as cliente_http:
        criar_coletor(settings_de_teste("adzuna, gupy"), cliente_http, AGORA, ["Niterói"]).coletar()

    parametros = [requisicao.url.params for requisicao in httpx_mock.get_requests()]

    assert [p.get("where") for p in parametros if "app_id" in p] == [None, "Niterói"]
    assert [p.get("city") for p in parametros if "jobName" in p] == [None, "Niterói"]


def test_cidades_de_interesse_vem_de_perfis_presenciais_e_hibridos_sem_repetir():
    usuarios = [
        usuario(1, "Rio de Janeiro, RJ", Modalidade.PRESENCIAL),
        usuario(2, "rio de janeiro, RJ", Modalidade.HIBRIDO),
        usuario(3, "Niterói, RJ", Modalidade.PRESENCIAL),
        usuario(4, "São Paulo, SP", Modalidade.REMOTO),
        usuario(5, "Curitiba, PR", Modalidade.INDIFERENTE),
    ]

    assert cidades_de_interesse(usuarios) == ["Niterói", "Rio de Janeiro", "rio de janeiro"]


def test_cidades_de_interesse_sem_usuarios_e_vazia():
    assert cidades_de_interesse([]) == []
