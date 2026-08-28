from datetime import UTC, date, datetime
from uuid import UUID

from radar.domain.models import Modalidade, Perfil, ResultadoMatch, Usuario, Vaga
from radar.notification.telegram import ErroDeNotificacao
from radar.pipeline import executar
from radar.storage.errors import ErroDeArmazenamento
from radar.storage.memoria import RepositorioEmMemoria

DATA_DE_TESTE = date(2026, 8, 26)
ID_USUARIO = UUID(int=1)
ID_OUTRO_USUARIO = UUID(int=2)


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
    def __init__(self, notas: dict[str, int]) -> None:
        self._notas = notas
        self.avaliadas: list[str] = []

    def avaliar(self, vagas: list[Vaga], perfil: Perfil) -> list[ResultadoMatch]:
        self.avaliadas.extend(vaga.id_externo for vaga in vagas)
        return [
            ResultadoMatch(
                vaga=vaga,
                nota=self._notas[vaga.id_externo],
                pontos_a_favor=[f"Ponto {vaga.id_externo}"],
            )
            for vaga in vagas
            if vaga.id_externo in self._notas
        ]


class NotificadorFalso:
    def __init__(self, chats_com_erro: set[str] = frozenset()) -> None:
        self.textos: list[str] = []
        self.chats: list[str] = []
        self._chats_com_erro = chats_com_erro

    def enviar(self, chat_id: str, texto: str) -> None:
        if chat_id in self._chats_com_erro:
            raise ErroDeNotificacao("chat not found")
        self.chats.append(chat_id)
        self.textos.append(texto)


class RepositorioFalso(RepositorioEmMemoria):
    def __init__(
        self,
        usuarios: list[Usuario],
        guardadas: list[ResultadoMatch] = (),
        enviadas: set[tuple[str, str]] = frozenset(),
        falha_ao_gravar: bool = False,
    ) -> None:
        super().__init__(usuarios)
        self._guardadas = list(guardadas)
        self._enviadas = set(enviadas)
        self._falha_ao_gravar = falha_ao_gravar
        self.registros: list[tuple[UUID, list[str], list[str], str]] = []

    def avaliacoes_existentes(self, usuario: Usuario, vagas: list[Vaga]) -> list[ResultadoMatch]:
        ids = {vaga.id_externo for vaga in vagas}
        return [resultado for resultado in self._guardadas if resultado.vaga.id_externo in ids]

    def ids_ja_enviadas(self, usuario: Usuario) -> set[tuple[str, str]]:
        return set(self._enviadas)

    def registrar(self, usuario, avaliadas, enviadas, modelo) -> None:
        if self._falha_ao_gravar:
            raise ErroDeArmazenamento("banco caiu")
        self.registros.append(
            (
                usuario.id,
                [resultado.vaga.id_externo for resultado in avaliadas],
                [resultado.vaga.id_externo for resultado in enviadas],
                modelo,
            )
        )


def usuario(id_usuario: UUID = ID_USUARIO, chat_id: str = "123") -> Usuario:
    return Usuario(id=id_usuario, perfil=perfil_exemplo(), chat_id=chat_id)


def rodar(
    vagas: list[Vaga],
    notas: dict[str, int],
    quantidade: int = 5,
    repositorio: RepositorioFalso | None = None,
    notificador: NotificadorFalso | None = None,
):
    notificador = notificador or NotificadorFalso()
    repositorio = repositorio or RepositorioFalso([usuario()])
    avaliador = AvaliadorFalso(notas)
    enviadas = executar(
        ColetorFalso(vagas),
        avaliador,
        notificador,
        repositorio,
        "modelo-teste",
        quantidade,
        DATA_DE_TESTE,
    )
    return enviadas.get(ID_USUARIO, []), notificador, avaliador


def test_envia_vagas_ordenadas_por_nota():
    selecionadas, notificador, _ = rodar([vaga(1), vaga(2), vaga(3)], {"1": 40, "2": 90, "3": 70})

    assert [resultado.vaga.id_externo for resultado in selecionadas] == ["2", "3", "1"]
    texto = notificador.textos[0]
    assert texto.index("Empresa 2") < texto.index("Empresa 3") < texto.index("Empresa 1")


def test_corta_na_quantidade_configurada():
    selecionadas, notificador, _ = rodar(
        [vaga(1), vaga(2), vaga(3)], {"1": 40, "2": 90, "3": 70}, quantidade=2
    )

    assert [resultado.nota for resultado in selecionadas] == [90, 70]
    assert "Empresa 1" not in notificador.textos[0]


def test_vaga_sem_resultado_do_avaliador_fica_fora_da_mensagem():
    selecionadas, notificador, _ = rodar([vaga(1), vaga(2)], {"2": 60})

    assert [resultado.vaga.id_externo for resultado in selecionadas] == ["2"]
    assert "Empresa 1" not in notificador.textos[0]


def test_aplica_o_prefiltro_antes_de_avaliar():
    selecionadas, _, _ = rodar(
        [vaga(1), vaga(2, titulo="Desenvolvedor Sênior Python")], {"1": 50, "2": 99}
    )

    assert [resultado.vaga.id_externo for resultado in selecionadas] == ["1"]


def test_mesma_vaga_em_duas_fontes_e_avaliada_e_enviada_uma_vez():
    da_adzuna = vaga(1)
    da_gupy = vaga(2).model_copy(update={"fonte": "gupy", "empresa": "Empresa 1"})

    selecionadas, notificador, avaliador = rodar([da_adzuna, da_gupy], {"1": 80, "2": 80})

    assert avaliador.avaliadas == ["1"]
    assert len(selecionadas) == 1
    assert notificador.textos[0].count("Empresa 1") == 1


def test_sem_vagas_envia_mensagem_de_nenhuma_vaga():
    selecionadas, notificador, _ = rodar([], {})

    assert selecionadas == []
    assert len(notificador.textos) == 1
    assert "Nenhuma vaga compatível" in notificador.textos[0]


def test_envia_para_cada_usuario_com_o_proprio_perfil():
    presencial = perfil_exemplo().model_copy(
        update={"modalidade": Modalidade.PRESENCIAL, "cidade": "São Paulo, SP"}
    )
    repositorio = RepositorioFalso(
        [usuario(), Usuario(id=ID_OUTRO_USUARIO, perfil=presencial, chat_id="456")]
    )
    notificador = NotificadorFalso()

    enviadas = executar(
        ColetorFalso([vaga(1)]),
        AvaliadorFalso({"1": 70}),
        notificador,
        repositorio,
        "modelo-teste",
        5,
        DATA_DE_TESTE,
    )

    assert notificador.chats == ["123", "456"]
    assert [resultado.nota for resultado in enviadas[ID_USUARIO]] == [70]
    assert enviadas[ID_OUTRO_USUARIO] == []


def test_erro_no_telegram_de_um_usuario_nao_bloqueia_os_outros():
    repositorio = RepositorioFalso([usuario(chat_id="bloqueado"), usuario(ID_OUTRO_USUARIO)])
    notificador = NotificadorFalso(chats_com_erro={"bloqueado"})

    enviadas = executar(
        ColetorFalso([vaga(1)]),
        AvaliadorFalso({"1": 70}),
        notificador,
        repositorio,
        "modelo-teste",
        5,
        DATA_DE_TESTE,
    )

    assert notificador.chats == ["123"]
    assert list(enviadas) == [ID_OUTRO_USUARIO]
    assert [registro[0] for registro in repositorio.registros] == [ID_OUTRO_USUARIO]


def test_vaga_ja_enviada_nao_e_reavaliada_nem_repetida():
    repositorio = RepositorioFalso([usuario()], enviadas={("adzuna", "1")})

    selecionadas, notificador, avaliador = rodar(
        [vaga(1), vaga(2)], {"1": 90, "2": 60}, repositorio=repositorio
    )

    assert avaliador.avaliadas == ["2"]
    assert [resultado.vaga.id_externo for resultado in selecionadas] == ["2"]
    assert "Empresa 1" not in notificador.textos[0]


def test_vaga_com_nota_guardada_nao_vai_ao_avaliador():
    guardada = ResultadoMatch(vaga=vaga(1), nota=95, pontos_a_favor=["Guardado"])
    repositorio = RepositorioFalso([usuario()], guardadas=[guardada])

    selecionadas, notificador, avaliador = rodar(
        [vaga(1), vaga(2)], {"1": 10, "2": 60}, repositorio=repositorio
    )

    assert avaliador.avaliadas == ["2"]
    assert [resultado.nota for resultado in selecionadas] == [95, 60]
    assert repositorio.registros == [(ID_USUARIO, ["2"], ["1", "2"], "modelo-teste")]


def test_falha_ao_gravar_nao_derruba_o_envio():
    repositorio = RepositorioFalso([usuario()], falha_ao_gravar=True)

    selecionadas, notificador, _ = rodar([vaga(1)], {"1": 70}, repositorio=repositorio)

    assert len(notificador.textos) == 1
    assert [resultado.nota for resultado in selecionadas] == [70]
