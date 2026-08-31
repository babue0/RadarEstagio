from datetime import UTC, datetime
from pathlib import Path

import httpx
from pytest_httpx import HTTPXMock

from radar.domain.models import Modalidade, Perfil, ResultadoMatch, Vaga
from radar.matching.enriquecimento import AvaliadorComDescricoesCompletas

CAMINHO_DA_PAGINA = Path(__file__).parent / "fixtures" / "adzuna_detalhe.html"


def perfil() -> Perfil:
    return Perfil(
        curso="Engenharia de Software",
        periodo=4,
        habilidades=["Python", "Java"],
        cidade="Rio de Janeiro, RJ",
        modalidade=Modalidade.PRESENCIAL,
    )


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


class AvaliadorEco:
    def avaliar(self, vagas: list[Vaga], perfil: Perfil) -> list[ResultadoMatch]:
        return [ResultadoMatch(vaga=vaga, nota=50) for vaga in vagas]


def test_avaliador_recebe_descricao_completa_da_pagina_da_adzuna(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://www.adzuna.com.br/details/5862521726",
        text=CAMINHO_DA_PAGINA.read_text(encoding="utf-8"),
    )
    with httpx.Client() as cliente:
        avaliador = AvaliadorComDescricoesCompletas(AvaliadorEco(), cliente)

        resultado = avaliador.avaliar([vaga_truncada()], perfil())[0]

    assert all(
        tecnologia in resultado.vaga.descricao for tecnologia in ("C#", "JavaScript", "SQL Server")
    )
    assert resultado.vaga.descricao_completa


def test_busca_a_pagina_da_mesma_vaga_uma_vez_por_execucao(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://www.adzuna.com.br/details/5862521726",
        text=CAMINHO_DA_PAGINA.read_text(encoding="utf-8"),
    )
    with httpx.Client() as cliente:
        avaliador = AvaliadorComDescricoesCompletas(AvaliadorEco(), cliente)

        avaliador.avaliar([vaga_truncada()], perfil())
        avaliador.avaliar([vaga_truncada()], perfil())

    assert len(httpx_mock.get_requests()) == 1


def test_nao_abre_pagina_de_vaga_que_nao_e_resumo_truncado(httpx_mock: HTTPXMock):
    completa = vaga_truncada().model_copy(
        update={"fonte": "gupy", "descricao": "Descrição completa da vaga"}
    )
    with httpx.Client() as cliente:
        avaliador = AvaliadorComDescricoesCompletas(AvaliadorEco(), cliente)

        resultado = avaliador.avaliar([completa], perfil())[0]

    assert resultado.vaga.descricao == "Descrição completa da vaga"
    assert httpx_mock.get_requests() == []


def test_mantem_descricao_marcada_como_incompleta_quando_pagina_falha(
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(
        url="https://www.adzuna.com.br/details/5862521726",
        status_code=503,
    )
    with httpx.Client() as cliente:
        avaliador = AvaliadorComDescricoesCompletas(AvaliadorEco(), cliente)

        resultado = avaliador.avaliar([vaga_truncada()], perfil())[0]

    assert not resultado.vaga.descricao_completa
