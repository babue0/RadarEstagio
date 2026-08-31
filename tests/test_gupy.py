import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
from pytest_httpx import HTTPXMock

from radar.collectors.errors import ErroDeColeta
from radar.collectors.gupy import RESULTADOS_POR_PAGINA, URL_BUSCA, ColetorGupy, limpar_html
from radar.domain.models import Modalidade

CAMINHO_DO_FIXTURE = Path(__file__).parent / "fixtures" / "gupy_resposta.json"
PUBLICADAS_DESDE = datetime(2026, 8, 20, tzinfo=UTC)


def resposta_gravada() -> dict:
    return json.loads(CAMINHO_DO_FIXTURE.read_text(encoding="utf-8"))


def resposta_vazia() -> dict:
    return {"data": [], "pagination": {"total": 0}}


def item(numero: int, publicada_em: str = "2026-08-26T10:00:00.000Z") -> dict:
    return {
        "id": numero,
        "name": f"Estágio {numero}",
        "description": "descrição",
        "careerPageName": "Empresa",
        "city": "São Paulo",
        "state": "São Paulo",
        "publishedDate": publicada_em,
        "jobUrl": f"https://empresa.gupy.io/job/{numero}",
        "workplaceType": "remote",
    }


@pytest.fixture
def coletor():
    with httpx.Client() as cliente_http:
        yield ColetorGupy(cliente_http, PUBLICADAS_DESDE, esperar=lambda _: None)


def test_converte_resposta_da_gupy_em_vagas(httpx_mock: HTTPXMock, coletor: ColetorGupy):
    httpx_mock.add_response(json=resposta_gravada())

    vagas = coletor.coletar()

    assert len(vagas) == 3
    primeira = vagas[0]
    assert primeira.id_externo == "12262661"
    assert primeira.fonte == "gupy"
    assert primeira.titulo == "Estagiário de TI - Vila Olímpia/SP"
    assert primeira.empresa == "LUZA GROUP BRASIL LTDA"
    assert primeira.localizacao == "São Paulo, São Paulo"
    assert primeira.descricao.startswith("Venha fazer parte de um ecossistema vivo")
    assert primeira.url.startswith("https://luzagroup.gupy.io/job/")
    assert primeira.publicada_em == datetime(2026, 8, 26, 13, 50, 23, 283000, tzinfo=UTC)


def test_mapeia_workplace_type_para_modalidade(httpx_mock: HTTPXMock, coletor: ColetorGupy):
    httpx_mock.add_response(json=resposta_gravada())

    modalidades = [vaga.modalidade for vaga in coletor.coletar()]

    assert modalidades == [Modalidade.PRESENCIAL, Modalidade.HIBRIDO, Modalidade.REMOTO]


def test_vaga_sem_cidade_recebe_localizacao_padrao(httpx_mock: HTTPXMock, coletor: ColetorGupy):
    httpx_mock.add_response(json=resposta_gravada())

    remota = coletor.coletar()[2]

    assert remota.localizacao == "Brasil"


def test_limpar_html_remove_tags_entidades_e_espacos_repetidos():
    sujo = "<p>Requisitos:</p><ul><li>Python&nbsp;3</li><li>Git &amp; GitHub</li></ul>\n\n Fim "

    assert limpar_html(sujo) == "Requisitos: Python 3 Git & GitHub Fim"


def test_busca_todos_os_estagios_do_pais_sem_termo(httpx_mock: HTTPXMock, coletor: ColetorGupy):
    httpx_mock.add_response(json=resposta_vazia())

    coletor.coletar()

    requisicao = httpx_mock.get_request()
    assert str(requisicao.url).startswith(URL_BUSCA)
    assert requisicao.url.params["jobName"] == ""
    assert requisicao.url.params["type"] == "vacancy_type_internship"
    assert requisicao.url.params["limit"] == str(RESULTADOS_POR_PAGINA)
    assert requisicao.url.params["offset"] == "0"
    assert "city" not in requisicao.url.params


def test_busca_tambem_por_cidade_dos_usuarios_presenciais(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=resposta_vazia(), is_reusable=True)
    with httpx.Client() as cliente_http:
        ColetorGupy(cliente_http, PUBLICADAS_DESDE, ["Rio de Janeiro", "Niterói"]).coletar()

    cidades = [requisicao.url.params.get("city") for requisicao in httpx_mock.get_requests()]

    assert cidades == [None, "Rio de Janeiro", "Niterói"]


def test_descarta_vagas_anteriores_a_data_limite(httpx_mock: HTTPXMock, coletor: ColetorGupy):
    antiga = item(2, publicada_em="2026-08-19T10:00:00.000Z")
    httpx_mock.add_response(json={"data": [item(1), antiga]})

    assert [vaga.id_externo for vaga in coletor.coletar()] == ["1"]


def test_data_de_publicacao_sem_fuso_e_tratada_como_utc(
    httpx_mock: HTTPXMock, coletor: ColetorGupy
):
    httpx_mock.add_response(json={"data": [item(1, publicada_em="2026-08-27")]})

    vagas = coletor.coletar()

    assert vagas[0].publicada_em == datetime(2026, 8, 27, tzinfo=UTC)


def test_vaga_antiga_com_data_sem_fuso_e_descartada(httpx_mock: HTTPXMock, coletor: ColetorGupy):
    httpx_mock.add_response(json={"data": [item(1, publicada_em="2026-08-19")]})

    assert coletor.coletar() == []


def test_vaga_sem_data_de_publicacao_e_ignorada(httpx_mock: HTTPXMock, coletor: ColetorGupy):
    sem_data = item(2)
    del sem_data["publishedDate"]
    httpx_mock.add_response(json={"data": [item(1), sem_data, item(3, publicada_em=None)]})

    assert [vaga.id_externo for vaga in coletor.coletar()] == ["1"]


def test_pagina_cheia_e_recente_busca_a_proxima_pagina(httpx_mock: HTTPXMock, coletor: ColetorGupy):
    pagina_cheia = [item(numero) for numero in range(1, RESULTADOS_POR_PAGINA + 1)]
    httpx_mock.add_response(json={"data": pagina_cheia})
    httpx_mock.add_response(json={"data": [item(RESULTADOS_POR_PAGINA + 1)]})

    vagas = coletor.coletar()

    assert len(vagas) == RESULTADOS_POR_PAGINA + 1
    offsets = [requisicao.url.params["offset"] for requisicao in httpx_mock.get_requests()[:2]]
    assert offsets == ["0", str(RESULTADOS_POR_PAGINA)]


def test_pagina_cheia_que_termina_em_vaga_antiga_encerra_a_busca(
    httpx_mock: HTTPXMock, coletor: ColetorGupy
):
    pagina = [item(numero) for numero in range(1, RESULTADOS_POR_PAGINA)]
    pagina.append(item(RESULTADOS_POR_PAGINA, publicada_em="2026-08-01T00:00:00.000Z"))
    httpx_mock.add_response(json={"data": pagina})

    vagas = coletor.coletar()

    assert len(vagas) == RESULTADOS_POR_PAGINA - 1
    assert len(httpx_mock.get_requests()) == 1


def test_mesma_vaga_no_pais_e_na_cidade_aparece_uma_vez(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"data": [item(1), item(2)]})
    httpx_mock.add_response(json={"data": [item(2), item(3)]})
    with httpx.Client() as cliente_http:
        vagas = ColetorGupy(cliente_http, PUBLICADAS_DESDE, ["Rio de Janeiro"]).coletar()

    assert [vaga.id_externo for vaga in vagas] == ["1", "2", "3"]


@pytest.mark.parametrize("status", [403, 429, 500])
def test_erro_http_levanta_erro_de_coleta(httpx_mock: HTTPXMock, coletor: ColetorGupy, status):
    httpx_mock.add_response(status_code=status, text="erro", is_reusable=True)

    with pytest.raises(ErroDeColeta) as capturado:
        coletor.coletar()

    assert str(status) in str(capturado.value)
    assert capturado.value.__cause__ is None


def test_falha_de_rede_levanta_erro_de_coleta(httpx_mock: HTTPXMock, coletor: ColetorGupy):
    httpx_mock.add_exception(httpx.ConnectError("conexão recusada"), is_reusable=True)

    with pytest.raises(ErroDeColeta, match="ConnectError"):
        coletor.coletar()


def test_erro_transitorio_e_tentado_de_novo_antes_de_desistir(httpx_mock: HTTPXMock):
    httpx_mock.add_response(status_code=503, text="indisponível")
    httpx_mock.add_response(json=resposta_vazia())
    esperas: list[float] = []
    with httpx.Client() as cliente_http:
        vagas = ColetorGupy(cliente_http, PUBLICADAS_DESDE, esperar=esperas.append).coletar()

    assert vagas == []
    assert esperas == [2]
