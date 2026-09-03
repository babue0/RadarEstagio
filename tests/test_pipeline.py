from datetime import UTC, datetime, timedelta
from uuid import UUID

from radar.domain.models import Modalidade, Perfil, ResultadoMatch, Usuario, Vaga
from radar.notification.telegram import ErroDeNotificacao
from radar.pipeline import ParametrosDaExecucao, executar
from radar.storage.errors import ErroDeArmazenamento
from radar.storage.memoria import RepositorioEmMemoria

AGORA_DE_TESTE = datetime(2026, 8, 26, 10, 23, tzinfo=UTC)
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
        modalidade=Modalidade.REMOTO,
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
        self.avaliacoes_gravadas: list[tuple[UUID, list[str], str]] = []
        self.envios_gravados: list[tuple[UUID, list[str]]] = []
        self.falhas_por_usuario: dict[UUID, int] = {}
        self.pausados: list[UUID] = []
        self.avisos_de_silencio: list[UUID] = []

    def avaliacoes_existentes(self, usuario: Usuario, vagas: list[Vaga]) -> list[ResultadoMatch]:
        ids = {vaga.id_externo for vaga in vagas}
        return [resultado for resultado in self._guardadas if resultado.vaga.id_externo in ids]

    def ids_ja_enviadas(self, usuario: Usuario) -> set[tuple[str, str]]:
        return set(self._enviadas)

    def guardar_avaliacoes(self, usuario, avaliadas, modelo) -> None:
        if self._falha_ao_gravar:
            raise ErroDeArmazenamento("banco caiu")
        self.avaliacoes_gravadas.append(
            (usuario.id, [resultado.vaga.id_externo for resultado in avaliadas], modelo)
        )

    def registrar_envios(self, usuario, enviadas) -> None:
        if self._falha_ao_gravar:
            raise ErroDeArmazenamento("banco caiu")
        self.falhas_por_usuario[usuario.id] = 0
        self.envios_gravados.append(
            (usuario.id, [resultado.vaga.id_externo for resultado in enviadas])
        )

    def registrar_falha_de_envio(self, usuario) -> int:
        if self._falha_ao_gravar:
            raise ErroDeArmazenamento("banco caiu")
        self.falhas_por_usuario[usuario.id] = self.falhas_por_usuario.get(usuario.id, 0) + 1
        return self.falhas_por_usuario[usuario.id]

    def registrar_aviso_de_silencio(self, usuario) -> None:
        self.avisos_de_silencio.append(usuario.id)

    def pausar(self, usuario) -> None:
        self.pausados.append(usuario.id)


def parametros(
    quantidade: int = 5,
    nota_minima: int = 0,
    falhas_ate_pausar: int = 3,
    dias_de_silencio_ate_avisar: int = 7,
) -> ParametrosDaExecucao:
    return ParametrosDaExecucao(
        modelo="modelo-teste",
        quantidade=quantidade,
        nota_minima=nota_minima,
        falhas_ate_pausar=falhas_ate_pausar,
        dias_de_silencio_ate_avisar=dias_de_silencio_ate_avisar,
    )


def usuario(
    id_usuario: UUID = ID_USUARIO,
    chat_id: str = "123",
    dias_sem_recomendacao: int | None = None,
    dias_desde_o_aviso: int | None = None,
) -> Usuario:
    return Usuario(
        id=id_usuario,
        perfil=perfil_exemplo(),
        chat_id=chat_id,
        sem_recomendacao_desde=(
            None
            if dias_sem_recomendacao is None
            else AGORA_DE_TESTE - timedelta(days=dias_sem_recomendacao)
        ),
        silencio_avisado_em=(
            None
            if dias_desde_o_aviso is None
            else AGORA_DE_TESTE - timedelta(days=dias_desde_o_aviso)
        ),
    )


def rodar(
    vagas: list[Vaga],
    notas: dict[str, int],
    quantidade: int = 5,
    nota_minima: int = 0,
    repositorio: RepositorioFalso | None = None,
    notificador: NotificadorFalso | None = None,
    falhas_ate_pausar: int = 3,
    agora: datetime = AGORA_DE_TESTE,
):
    notificador = notificador or NotificadorFalso()
    repositorio = repositorio or RepositorioFalso([usuario()])
    avaliador = AvaliadorFalso(notas)
    resumo = executar(
        ColetorFalso(vagas),
        avaliador,
        notificador,
        repositorio,
        parametros(
            quantidade=quantidade,
            nota_minima=nota_minima,
            falhas_ate_pausar=falhas_ate_pausar,
        ),
        agora,
    )
    return resumo.enviadas_por_usuario.get(ID_USUARIO, []), notificador, avaliador


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


def test_vaga_abaixo_da_nota_minima_fica_fora_da_mensagem():
    selecionadas, notificador, _ = rodar(
        [vaga(1), vaga(2), vaga(3)], {"1": 35, "2": 90, "3": 60}, nota_minima=60
    )

    assert [resultado.nota for resultado in selecionadas] == [90, 60]
    assert "Empresa 1" not in notificador.textos[0]


def test_todas_abaixo_da_nota_minima_nao_manda_mensagem():
    selecionadas, notificador, _ = rodar([vaga(1), vaga(2)], {"1": 35, "2": 20}, nota_minima=60)

    assert selecionadas == []
    assert notificador.textos == []


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


def test_sem_vagas_nao_manda_mensagem():
    selecionadas, notificador, _ = rodar([], {})

    assert selecionadas == []
    assert notificador.textos == []


def test_envia_para_cada_usuario_com_o_proprio_perfil():
    presencial = perfil_exemplo().model_copy(
        update={"modalidade": Modalidade.PRESENCIAL, "cidade": "São Paulo, SP"}
    )
    repositorio = RepositorioFalso(
        [usuario(), Usuario(id=ID_OUTRO_USUARIO, perfil=presencial, chat_id="456")]
    )
    notificador = NotificadorFalso()

    resumo = executar(
        ColetorFalso([vaga(1)]),
        AvaliadorFalso({"1": 70}),
        notificador,
        repositorio,
        parametros(),
        AGORA_DE_TESTE,
    )

    assert notificador.chats == ["123"]
    assert [resultado.nota for resultado in resumo.enviadas_por_usuario[ID_USUARIO]] == [70]
    assert ID_OUTRO_USUARIO not in resumo.enviadas_por_usuario
    assert resumo.usuarios == 2
    assert resumo.atendidos() == 1
    assert resumo.vagas_enviadas() == 1


def test_erro_no_telegram_de_um_usuario_nao_bloqueia_os_outros():
    repositorio = RepositorioFalso([usuario(chat_id="bloqueado"), usuario(ID_OUTRO_USUARIO)])
    notificador = NotificadorFalso(chats_com_erro={"bloqueado"})

    resumo = executar(
        ColetorFalso([vaga(1)]),
        AvaliadorFalso({"1": 70}),
        notificador,
        repositorio,
        parametros(),
        AGORA_DE_TESTE,
    )

    assert notificador.chats == ["123"]
    assert list(resumo.enviadas_por_usuario) == [ID_OUTRO_USUARIO]
    assert [registro[0] for registro in repositorio.envios_gravados] == [ID_OUTRO_USUARIO]


def test_vaga_ja_enviada_nao_e_reavaliada_nem_repetida():
    repositorio = RepositorioFalso([usuario()], enviadas={("adzuna", "1")})

    selecionadas, notificador, avaliador = rodar(
        [vaga(1), vaga(2)], {"1": 90, "2": 60}, repositorio=repositorio
    )

    assert avaliador.avaliadas == ["2"]
    assert [resultado.vaga.id_externo for resultado in selecionadas] == ["2"]
    assert "Empresa 1" not in notificador.textos[0]


def test_avaliacao_toda_bloqueada_nao_manda_mensagem_enganosa():
    selecionadas, notificador, _ = rodar([vaga(1), vaga(2)], {})

    assert selecionadas == []
    assert notificador.textos == []


def test_vaga_com_nota_guardada_nao_vai_ao_avaliador():
    guardada = ResultadoMatch(vaga=vaga(1), nota=95, pontos_a_favor=["Guardado"])
    repositorio = RepositorioFalso([usuario()], guardadas=[guardada])

    selecionadas, notificador, avaliador = rodar(
        [vaga(1), vaga(2)], {"1": 10, "2": 60}, repositorio=repositorio
    )

    assert avaliador.avaliadas == ["2"]
    assert [resultado.nota for resultado in selecionadas] == [95, 60]
    assert repositorio.avaliacoes_gravadas == [(ID_USUARIO, ["2"], "modelo-teste")]
    assert repositorio.envios_gravados == [(ID_USUARIO, ["1", "2"])]


def test_aplica_regras_objetivas_na_nota_guardada():
    sem_modalidade = vaga(1).model_copy(update={"modalidade": None})
    guardada = ResultadoMatch(
        vaga=sem_modalidade,
        nota=95,
        pontos_a_favor=["Python informado"],
        pontos_contra=["Modalidade não informada", "SQL não informado"],
    )
    repositorio = RepositorioFalso([usuario()], guardadas=[guardada])

    selecionadas, notificador, avaliador = rodar([sem_modalidade], {}, repositorio=repositorio)

    assert avaliador.avaliadas == []
    assert selecionadas[0].nota == 95
    assert selecionadas[0].pontos_contra == ["SQL não informado"]
    assert "❌ SQL não informado" in notificador.textos[0]
    assert "⚠️" not in notificador.textos[0]


def test_avaliacao_e_gravada_mesmo_quando_o_telegram_falha():
    repositorio = RepositorioFalso([usuario(chat_id="bloqueado")])
    notificador = NotificadorFalso(chats_com_erro={"bloqueado"})

    rodar([vaga(1)], {"1": 70}, repositorio=repositorio, notificador=notificador)

    assert repositorio.avaliacoes_gravadas == [(ID_USUARIO, ["1"], "modelo-teste")]
    assert repositorio.envios_gravados == []


def test_falhas_seguidas_de_envio_pausam_o_perfil():
    repositorio = RepositorioFalso([usuario(chat_id="bloqueado")])
    notificador = NotificadorFalso(chats_com_erro={"bloqueado"})

    for _ in range(3):
        rodar(
            [vaga(1)],
            {"1": 70},
            repositorio=repositorio,
            notificador=notificador,
            falhas_ate_pausar=3,
        )

    assert repositorio.falhas_por_usuario == {ID_USUARIO: 3}
    assert repositorio.pausados == [ID_USUARIO]


def test_envio_bem_sucedido_zera_as_falhas_acumuladas():
    repositorio = RepositorioFalso([usuario()])
    repositorio.falhas_por_usuario[ID_USUARIO] = 2

    rodar([vaga(1)], {"1": 70}, repositorio=repositorio)

    assert repositorio.falhas_por_usuario == {ID_USUARIO: 0}
    assert repositorio.pausados == []


def test_falha_ao_gravar_nao_derruba_o_envio():
    repositorio = RepositorioFalso([usuario()], falha_ao_gravar=True)

    selecionadas, notificador, _ = rodar([vaga(1)], {"1": 70}, repositorio=repositorio)

    assert len(notificador.textos) == 1
    assert [resultado.nota for resultado in selecionadas] == [70]


def test_silencio_prolongado_gera_um_aviso_semanal():
    repositorio = RepositorioFalso([usuario(dias_sem_recomendacao=8)])

    selecionadas, notificador, _ = rodar([], {}, repositorio=repositorio)

    assert selecionadas == []
    assert "nos últimos 7 dias" in notificador.textos[0]
    assert repositorio.avisos_de_silencio == [ID_USUARIO]


def test_aviso_de_silencio_nao_se_repete_todo_dia():
    repositorio = RepositorioFalso([usuario(dias_sem_recomendacao=20, dias_desde_o_aviso=2)])

    _, notificador, _ = rodar([], {}, repositorio=repositorio)

    assert notificador.textos == []
    assert repositorio.avisos_de_silencio == []


def test_usuario_recente_sem_vagas_fica_em_silencio():
    repositorio = RepositorioFalso([usuario(dias_sem_recomendacao=2)])

    _, notificador, _ = rodar([], {}, repositorio=repositorio)

    assert notificador.textos == []
    assert repositorio.avisos_de_silencio == []
