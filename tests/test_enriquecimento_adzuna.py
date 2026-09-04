from datetime import UTC, datetime
from pathlib import Path

import httpx
from pytest_httpx import HTTPXMock

from radar.domain.models import Vaga
from radar.matching.enriquecimento import EnriquecedorDeDescricoes

CAMINHO_DA_PAGINA = Path(__file__).parent / "fixtures" / "adzuna_detalhe.html"


def vaga_truncada() -> Vaga:
    return Vaga(
        id_externo="5862521726",
        fonte="adzuna",
        titulo="Estágio Ti Desenvolvimento",
        empresa="Trinks",
        localizacao="Rio de Janeiro",
        descricao="Atuar com um time e contar com o auxílio de profi".ljust(499, " ") + "…",
        url="https://www.adzuna.com.br/details/5862521726",
        publicada_em=datetime(2026, 8, 31, tzinfo=UTC),
        descricao_completa=False,
    )


def test_devolve_a_vaga_com_descricao_completa_da_pagina_da_adzuna(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://www.adzuna.com.br/details/5862521726",
        text=CAMINHO_DA_PAGINA.read_text(encoding="utf-8"),
    )
    with httpx.Client() as cliente:
        enriquecidas = EnriquecedorDeDescricoes(cliente).enriquecer([vaga_truncada()])

    assert all(
        tecnologia in enriquecidas[0].descricao for tecnologia in ("C#", "JavaScript", "SQL Server")
    )
    assert enriquecidas[0].descricao_completa


def test_busca_a_pagina_da_mesma_vaga_uma_vez_por_execucao(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://www.adzuna.com.br/details/5862521726",
        text=CAMINHO_DA_PAGINA.read_text(encoding="utf-8"),
    )
    with httpx.Client() as cliente:
        enriquecedor = EnriquecedorDeDescricoes(cliente)

        enriquecedor.enriquecer([vaga_truncada()])
        enriquecedor.enriquecer([vaga_truncada()])

    assert len(httpx_mock.get_requests()) == 1


def test_nao_abre_pagina_de_vaga_que_nao_e_resumo_truncado(httpx_mock: HTTPXMock):
    completa = vaga_truncada().model_copy(
        update={"fonte": "gupy", "descricao": "Descrição completa da vaga"}
    )
    with httpx.Client() as cliente:
        enriquecidas = EnriquecedorDeDescricoes(cliente).enriquecer([completa])

    assert enriquecidas[0].descricao == "Descrição completa da vaga"
    assert httpx_mock.get_requests() == []


def test_mantem_descricao_marcada_como_incompleta_quando_pagina_falha(
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(
        url="https://www.adzuna.com.br/details/5862521726",
        status_code=503,
    )
    with httpx.Client() as cliente:
        enriquecidas = EnriquecedorDeDescricoes(cliente).enriquecer([vaga_truncada()])

    assert not enriquecidas[0].descricao_completa
