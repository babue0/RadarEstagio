import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
from pytest_httpx import HTTPXMock

from radar.collectors.adzuna import URL_BUSCA, ColetorAdzuna
from radar.collectors.errors import ErroDeColeta
from radar.settings import Settings

CAMINHO_DO_FIXTURE = Path(__file__).parent / "fixtures" / "adzuna_resposta.json"
APP_KEY_DE_TESTE = "app-key-de-teste"


def settings_de_teste() -> Settings:
    return Settings(
        _env_file=None,
        adzuna_app_id="app-id-de-teste",
        adzuna_app_key=APP_KEY_DE_TESTE,
        gemini_api_key="gemini-de-teste",
        telegram_bot_token="token-de-teste",
        telegram_chat_id="123",
        dias_recentes=3,
    )


def resposta_gravada() -> dict:
    return json.loads(CAMINHO_DO_FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture
def coletor():
    with httpx.Client() as cliente_http:
        yield ColetorAdzuna(settings_de_teste(), cliente_http)


def test_converte_resposta_da_adzuna_em_vagas(httpx_mock: HTTPXMock, coletor: ColetorAdzuna):
    httpx_mock.add_response(json=resposta_gravada())

    vagas = coletor.coletar()

    assert len(vagas) == 3
    primeira = vagas[0]
    assert primeira.id_externo == "5855737878"
    assert primeira.fonte == "adzuna"
    assert primeira.titulo == "Vaga de Estágio em TI"
    assert primeira.empresa == "Premier Logistcs"
    assert primeira.localizacao == "Salvador, Bahia"
    assert primeira.descricao.startswith("Estamos em busca de um(a) Estagiário(a) de TI")
    assert primeira.url == (
        "https://www.adzuna.com.br/details/5855737878?utm_medium=api&utm_source=teste"
    )
    assert primeira.publicada_em == datetime(2026, 8, 25, 18, 49, 50, tzinfo=UTC)


def test_envia_credenciais_e_filtros_na_busca(httpx_mock: HTTPXMock, coletor: ColetorAdzuna):
    httpx_mock.add_response(json={"results": []})

    coletor.coletar()

    requisicao = httpx_mock.get_request()
    assert requisicao.method == "GET"
    assert str(requisicao.url).startswith(URL_BUSCA)
    parametros = requisicao.url.params
    assert parametros["app_id"] == "app-id-de-teste"
    assert parametros["app_key"] == APP_KEY_DE_TESTE
    assert parametros["what"] == "estágio"
    assert parametros["category"] == "it-jobs"
    assert parametros["max_days_old"] == "3"
    assert parametros["results_per_page"] == "50"


def test_resposta_sem_resultados_retorna_lista_vazia(httpx_mock: HTTPXMock, coletor: ColetorAdzuna):
    httpx_mock.add_response(json={"count": 0, "results": []})

    assert coletor.coletar() == []


@pytest.mark.parametrize("status", [401, 403, 429, 500])
def test_erro_http_levanta_erro_de_coleta_sem_expor_credenciais(
    httpx_mock: HTTPXMock, coletor: ColetorAdzuna, status: int
):
    httpx_mock.add_response(status_code=status, json={"exception": "erro"})

    with pytest.raises(ErroDeColeta) as capturado:
        coletor.coletar()

    assert str(status) in str(capturado.value)
    assert APP_KEY_DE_TESTE not in str(capturado.value)
    assert capturado.value.__cause__ is None


def test_falha_de_rede_levanta_erro_de_coleta(httpx_mock: HTTPXMock, coletor: ColetorAdzuna):
    httpx_mock.add_exception(httpx.ConnectError("conexão recusada"))

    with pytest.raises(ErroDeColeta, match="ConnectError"):
        coletor.coletar()


def test_coletas_sucessivas_nao_compartilham_estado(httpx_mock: HTTPXMock, coletor: ColetorAdzuna):
    httpx_mock.add_response(json=resposta_gravada())
    httpx_mock.add_response(json={"results": []})

    primeira_coleta = coletor.coletar()
    segunda_coleta = coletor.coletar()

    assert len(primeira_coleta) == 3
    assert segunda_coleta == []
