from datetime import UTC, datetime

import pytest

from radar.collectors.composto import ColetorComposto
from radar.collectors.errors import ErroDeColeta
from radar.domain.models import Vaga


def vaga(fonte: str, numero: int) -> Vaga:
    return Vaga(
        id_externo=str(numero),
        fonte=fonte,
        titulo=f"Estágio {numero}",
        empresa="Empresa",
        localizacao="Rio de Janeiro",
        descricao="descrição",
        url=f"https://{fonte}.com/vaga/{numero}",
        publicada_em=datetime(2026, 8, 25, tzinfo=UTC),
    )


class ColetorFalso:
    def __init__(self, vagas: list[Vaga]) -> None:
        self._vagas = vagas

    def coletar(self) -> list[Vaga]:
        return self._vagas


class ColetorQueFalha:
    def coletar(self) -> list[Vaga]:
        raise ErroDeColeta("HTTP 500")


def test_soma_as_vagas_de_todas_as_fontes_na_ordem_configurada():
    composto = ColetorComposto(
        {
            "adzuna": ColetorFalso([vaga("adzuna", 1), vaga("adzuna", 2)]),
            "gupy": ColetorFalso([vaga("gupy", 3)]),
        }
    )

    vagas = composto.coletar()

    assert [(vaga.fonte, vaga.id_externo) for vaga in vagas] == [
        ("adzuna", "1"),
        ("adzuna", "2"),
        ("gupy", "3"),
    ]


def test_fonte_que_falha_e_ignorada_e_as_outras_continuam(caplog: pytest.LogCaptureFixture):
    composto = ColetorComposto(
        {"adzuna": ColetorQueFalha(), "gupy": ColetorFalso([vaga("gupy", 1)])}
    )

    with caplog.at_level("WARNING"):
        vagas = composto.coletar()

    assert [vaga.id_externo for vaga in vagas] == ["1"]
    assert "adzuna" in caplog.text
    assert "HTTP 500" in caplog.text


def test_todas_as_fontes_falhando_levanta_erro_de_coleta():
    composto = ColetorComposto({"adzuna": ColetorQueFalha(), "gupy": ColetorQueFalha()})

    with pytest.raises(ErroDeColeta, match="Nenhuma fonte respondeu"):
        composto.coletar()


def test_sem_coletores_e_rejeitado():
    with pytest.raises(ValueError):
        ColetorComposto({})
