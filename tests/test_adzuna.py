import json
import re
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
from pytest_httpx import HTTPXMock

from radar.collectors.adzuna import (
    LIMITE_DE_PAGINAS_POR_REGIAO,
    RESULTADOS_POR_PAGINA,
    URL_BUSCA,
    ColetorAdzuna,
)
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


def item(numero: int, area: list[str] | None = None) -> dict:
    modelo = resposta_gravada()["results"][0]
    modelo["id"] = numero
    if area is not None:
        modelo["location"] = {"display_name": ", ".join(reversed(area[-2:])), "area": area}
    return modelo


def url_da_pagina(pagina: int) -> re.Pattern[str]:
    return re.compile(re.escape(f"{URL_BUSCA}/{pagina}?"))


def pagina_cheia(inicio: int) -> dict:
    return {"results": [item(numero) for numero in range(inicio, inicio + RESULTADOS_POR_PAGINA)]}


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


def test_vaga_sem_empresa_ou_localizacao_recebe_valores_padrao(
    httpx_mock: HTTPXMock, coletor: ColetorAdzuna
):
    item = resposta_gravada()["results"][0]
    item["company"] = {"__CLASS__": "Adzuna::API::Response::Company"}
    del item["location"]
    httpx_mock.add_response(json={"results": [item]})

    vaga = coletor.coletar()[0]

    assert vaga.empresa == "Empresa não informada"
    assert vaga.localizacao == "Brasil"


def test_marca_resumo_de_500_caracteres_como_descricao_incompleta(
    httpx_mock: HTTPXMock, coletor: ColetorAdzuna
):
    resumido = item(1)
    resumido["description"] = "x" * 499 + "…"
    httpx_mock.add_response(json={"results": [resumido]})

    vaga = coletor.coletar()[0]

    assert not vaga.descricao_completa


def test_envia_credenciais_e_filtros_na_busca(httpx_mock: HTTPXMock, coletor: ColetorAdzuna):
    httpx_mock.add_response(json={"results": []})

    coletor.coletar()

    requisicao = httpx_mock.get_request()
    assert requisicao.method == "GET"
    assert str(requisicao.url).startswith(URL_BUSCA)
    parametros = requisicao.url.params
    assert parametros["app_id"] == "app-id-de-teste"
    assert parametros["app_key"] == APP_KEY_DE_TESTE
    assert parametros["what_and"] == "estágio"
    assert "tecnologia" in parametros["what_or"]
    assert "category" not in parametros
    assert "where" not in parametros
    assert parametros["max_days_old"] == "3"
    assert parametros["results_per_page"] == "50"


def test_busca_tambem_por_cidade_dos_usuarios_presenciais(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"results": []}, is_reusable=True)
    with httpx.Client() as cliente_http:
        ColetorAdzuna(settings_de_teste(), cliente_http, ["Rio de Janeiro", "Niterói"]).coletar()

    locais = [requisicao.url.params.get("where") for requisicao in httpx_mock.get_requests()]

    assert locais == [None, "Rio de Janeiro", "Niterói"]


def test_pagina_cheia_busca_a_proxima_pagina(httpx_mock: HTTPXMock, coletor: ColetorAdzuna):
    httpx_mock.add_response(url=url_da_pagina(1), json=pagina_cheia(1))
    httpx_mock.add_response(url=url_da_pagina(2), json={"results": [item(999)]})

    vagas = coletor.coletar()

    assert len(vagas) == RESULTADOS_POR_PAGINA + 1
    assert len(httpx_mock.get_requests()) == 2


def test_respeita_o_limite_de_paginas(httpx_mock: HTTPXMock, coletor: ColetorAdzuna):
    for pagina in range(1, LIMITE_DE_PAGINAS_POR_REGIAO + 1):
        inicio = pagina * RESULTADOS_POR_PAGINA
        httpx_mock.add_response(url=url_da_pagina(pagina), json=pagina_cheia(inicio))

    vagas = coletor.coletar()

    assert len(vagas) == LIMITE_DE_PAGINAS_POR_REGIAO * RESULTADOS_POR_PAGINA
    assert len(httpx_mock.get_requests()) == LIMITE_DE_PAGINAS_POR_REGIAO


def test_mesma_vaga_no_pais_e_na_cidade_aparece_uma_vez(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"results": [item(1), item(2)]})
    httpx_mock.add_response(json={"results": [item(2), item(3)]})
    with httpx.Client() as cliente_http:
        vagas = ColetorAdzuna(settings_de_teste(), cliente_http, ["Rio de Janeiro"]).coletar()

    assert [vaga.id_externo for vaga in vagas] == ["1", "2", "3"]


def test_localizacao_usa_cidade_e_estado_mesmo_quando_ha_bairro(
    httpx_mock: HTTPXMock, coletor: ColetorAdzuna
):
    com_bairro = item(
        1, area=["Brasil", "Sudeste", "Estado do Rio de Janeiro", "Rio de Janeiro", "Copacabana"]
    )
    httpx_mock.add_response(json={"results": [com_bairro]})

    assert coletor.coletar()[0].localizacao == "Rio de Janeiro, Estado do Rio de Janeiro"


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
