from datetime import UTC, date, datetime

from radar.domain.models import Modalidade, Perfil, ResultadoMatch, Vaga
from radar.matching.gemini import ErroDeAvaliacao
from radar.pipeline import executar

DATA_DE_TESTE = date(2026, 8, 26)


def vaga(numero: int, titulo: str = "Estágio Python") -> Vaga:
    return Vaga(
        id_externo=str(numero),
        fonte="adzuna",
        titulo=titulo,
        empresa=f"Empresa {numero}",
        localizacao="Rio de Janeiro",
        descricao="descrição",
        url=f"https://exemplo.com/vaga/{numero}",
        publicada_em=datetime(2026, 8, 25, tzinfo=UTC),
    )


def perfil_exemplo() -> Perfil:
    return Perfil(
        curso="Engenharia de Software",
        periodo=4,
        habilidades=["Python"],
        cidade="Rio de Janeiro, RJ",
        modalidade=Modalidade.REMOTO,
    )


class ColetorFalso:
    def __init__(self, vagas: list[Vaga]) -> None:
        self._vagas = vagas

    def coletar(self) -> list[Vaga]:
        return self._vagas


class AvaliadorFalso:
    def __init__(self, notas: dict[str, int | Exception]) -> None:
        self._notas = notas

    def avaliar(self, vaga: Vaga, perfil: Perfil) -> ResultadoMatch:
        nota = self._notas[vaga.id_externo]
        if isinstance(nota, Exception):
            raise nota
        return ResultadoMatch(vaga=vaga, nota=nota, motivo=f"Motivo {vaga.id_externo}")


class NotificadorFalso:
    def __init__(self) -> None:
        self.textos: list[str] = []

    def enviar(self, texto: str) -> None:
        self.textos.append(texto)


def rodar(vagas: list[Vaga], notas: dict[str, int | Exception], quantidade: int = 5):
    notificador = NotificadorFalso()
    selecionadas = executar(
        ColetorFalso(vagas),
        AvaliadorFalso(notas),
        notificador,
        perfil_exemplo(),
        quantidade,
        DATA_DE_TESTE,
    )
    return selecionadas, notificador


def test_envia_vagas_ordenadas_por_nota():
    selecionadas, notificador = rodar([vaga(1), vaga(2), vaga(3)], {"1": 40, "2": 90, "3": 70})

    assert [resultado.vaga.id_externo for resultado in selecionadas] == ["2", "3", "1"]
    texto = notificador.textos[0]
    assert texto.index("Empresa 2") < texto.index("Empresa 3") < texto.index("Empresa 1")


def test_corta_na_quantidade_configurada():
    selecionadas, notificador = rodar(
        [vaga(1), vaga(2), vaga(3)], {"1": 40, "2": 90, "3": 70}, quantidade=2
    )

    assert [resultado.nota for resultado in selecionadas] == [90, 70]
    assert "Empresa 1" not in notificador.textos[0]


def test_vaga_com_erro_de_avaliacao_e_ignorada_sem_derrubar_o_run():
    selecionadas, notificador = rodar(
        [vaga(1), vaga(2)], {"1": ErroDeAvaliacao("Gemini respondeu HTTP 503"), "2": 60}
    )

    assert [resultado.vaga.id_externo for resultado in selecionadas] == ["2"]
    assert "Empresa 2" in notificador.textos[0]
    assert "Empresa 1" not in notificador.textos[0]


def test_aplica_o_prefiltro_antes_de_avaliar():
    selecionadas, _ = rodar(
        [vaga(1), vaga(2, titulo="Desenvolvedor Sênior Python")], {"1": 50, "2": 99}
    )

    assert [resultado.vaga.id_externo for resultado in selecionadas] == ["1"]


def test_sem_vagas_envia_mensagem_de_nenhuma_vaga():
    selecionadas, notificador = rodar([], {})

    assert selecionadas == []
    assert len(notificador.textos) == 1
    assert "Nenhuma vaga compatível" in notificador.textos[0]
