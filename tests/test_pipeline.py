from datetime import UTC, datetime, timedelta
from uuid import UUID

from radar.domain.models import (
    AreaDeInteresse,
    ExtracaoDaVaga,
    Modalidade,
    NivelCompatibilidade,
    Perfil,
    PerguntaDeFeedback,
    RecusasDoUsuario,
    ResultadoMatch,
    Usuario,
    Vaga,
)
from radar.notification.telegram import ErroDeNotificacao
from radar.pipeline import ParametrosDaExecucao, executar
from radar.storage.errors import ErroDeArmazenamento
from radar.storage.memoria import RepositorioEmMemoria

AGORA_DE_TESTE = datetime(2026, 8, 26, 10, 23, tzinfo=UTC)
URL_DE_RASTREIO = "https://projeto.supabase.co/functions/v1/ir"
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


class ExtratorFalso:
    def __init__(self, notas: dict[str, int]) -> None:
        self._notas = notas
        self.extraidas: list[str] = []

    def extrair(self, vagas: list[Vaga]) -> list[ExtracaoDaVaga]:
        self.extraidas.extend(vaga.id_externo for vaga in vagas)
        return [
            ExtracaoDaVaga(
                id_vaga=vaga.id_externo,
                area_de_tecnologia=NivelCompatibilidade.COMPATIVEL,
            )
            for vaga in vagas
        ]


class PontuadorFalso:
    def __init__(self, notas: dict[str, int]) -> None:
        self._notas = notas
        self.pontuadas: list[str] = []

    def __call__(
        self, vagas: list[Vaga], extracoes: dict[str, ExtracaoDaVaga], perfil: Perfil
    ) -> list[ResultadoMatch]:
        self.pontuadas.extend(vaga.id_externo for vaga in vagas)
        return [
            ResultadoMatch(
                vaga=vaga,
                nota=self._notas[vaga.id_externo],
                pontos_a_favor=[f"Ponto {vaga.id_externo}"],
            )
            for vaga in vagas
            if vaga.id_externo in self._notas and vaga.id_externo in extracoes
        ]


class NotificadorFalso:
    def __init__(self, chats_com_erro: set[str] = frozenset()) -> None:
        self.textos: list[str] = []
        self.chats: list[str] = []
        self.perguntas: list[PerguntaDeFeedback] = []
        self._chats_com_erro = chats_com_erro

    def enviar(self, chat_id: str, texto: str) -> None:
        if chat_id in self._chats_com_erro:
            raise ErroDeNotificacao("chat not found")
        self.chats.append(chat_id)
        self.textos.append(texto)

    def enviar_pergunta(self, chat_id: str, pergunta: PerguntaDeFeedback) -> None:
        if chat_id in self._chats_com_erro:
            raise ErroDeNotificacao("chat not found")
        self.perguntas.append(pergunta)


class RepositorioFalso(RepositorioEmMemoria):
    def __init__(
        self,
        usuarios: list[Usuario],
        guardadas: list[ResultadoMatch] = (),
        enviadas: set[tuple[str, str]] = frozenset(),
        falha_ao_gravar: bool = False,
        enviadas_recentes: list[Vaga] = (),
        recusas: RecusasDoUsuario | None = None,
    ) -> None:
        super().__init__(usuarios)
        self._guardadas = list(guardadas)
        self._enviadas = set(enviadas)
        self._enviadas_recentes = list(enviadas_recentes)
        self._recusas = recusas or RecusasDoUsuario()
        self._falha_ao_gravar = falha_ao_gravar
        self.avaliacoes_gravadas: list[tuple[UUID, list[str], str]] = []
        self.envios_gravados: list[tuple[UUID, list[str]]] = []
        self.falhas_por_usuario: dict[UUID, int] = {}
        self.pausados: list[UUID] = []
        self.avisos_de_silencio: list[UUID] = []
        self.carencias_aplicadas: list[int] = []
        self.extracoes_guardadas: dict[str, ExtracaoDaVaga] = {}
        self.tokens_gravados: list[UUID] = []
        self.gravacoes_de_extracao = 0

    def extracoes_existentes(self, vagas: list[Vaga]) -> dict[str, ExtracaoDaVaga]:
        ids = {vaga.id_externo for vaga in vagas}
        return {
            id_vaga: extracao
            for id_vaga, extracao in self.extracoes_guardadas.items()
            if id_vaga in ids
        }

    def guardar_extracoes(self, extracoes: list[tuple[Vaga, ExtracaoDaVaga]], modelo: str) -> None:
        self.gravacoes_de_extracao += 1
        for vaga_extraida, extracao in extracoes:
            self.extracoes_guardadas[vaga_extraida.id_externo] = extracao

    def avaliacoes_existentes(self, usuario: Usuario, vagas: list[Vaga]) -> list[ResultadoMatch]:
        ids = {vaga.id_externo for vaga in vagas}
        return [resultado for resultado in self._guardadas if resultado.vaga.id_externo in ids]

    def ids_ja_enviadas(self, usuario: Usuario) -> set[tuple[str, str]]:
        return set(self._enviadas)

    def vagas_enviadas_recentemente(self, usuario: Usuario) -> list[Vaga]:
        return list(self._enviadas_recentes)

    def recusas_do_usuario(self, usuario: Usuario) -> RecusasDoUsuario:
        return self._recusas

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
            (usuario.id, [item.resultado.vaga.id_externo for item in enviadas])
        )
        self.tokens_gravados.extend(item.token for item in enviadas)

    def registrar_falha_de_envio(self, usuario) -> int:
        if self._falha_ao_gravar:
            raise ErroDeArmazenamento("banco caiu")
        self.falhas_por_usuario[usuario.id] = self.falhas_por_usuario.get(usuario.id, 0) + 1
        return self.falhas_por_usuario[usuario.id]

    def apagar_contas_excluidas(self, dias_de_carencia: int) -> int:
        self.carencias_aplicadas.append(dias_de_carencia)
        return 0

    def registrar_aviso_de_silencio(self, usuario) -> None:
        self.avisos_de_silencio.append(usuario.id)

    def pausar(self, usuario) -> None:
        self.pausados.append(usuario.id)


def parametros(
    quantidade: int = 5,
    nota_minima: int = 0,
    falhas_ate_pausar: int = 3,
    dias_de_silencio_ate_avisar: int = 7,
    url_de_rastreio: str = "",
    dias_ate_apagar_conta_excluida: int = 60,
) -> ParametrosDaExecucao:
    return ParametrosDaExecucao(
        modelo="modelo-teste",
        quantidade=quantidade,
        nota_minima=nota_minima,
        falhas_ate_pausar=falhas_ate_pausar,
        dias_de_silencio_ate_avisar=dias_de_silencio_ate_avisar,
        url_de_rastreio=url_de_rastreio,
        dias_ate_apagar_conta_excluida=dias_ate_apagar_conta_excluida,
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


def test_vaga_enriquecida_e_pontuada_com_a_descricao_completa():
    truncada = vaga(1).model_copy(update={"descricao_completa": False})
    notificador = NotificadorFalso()
    repositorio = RepositorioFalso([usuario()])

    def completar_descricoes(vagas: list[Vaga]) -> list[Vaga]:
        return [item.model_copy(update={"descricao_completa": True}) for item in vagas]

    resumo = executar(
        ColetorFalso([truncada]),
        ExtratorFalso({"1": 90}),
        notificador,
        repositorio,
        parametros(),
        AGORA_DE_TESTE,
        PontuadorFalso({"1": 90}),
        enriquecer=completar_descricoes,
    )

    selecionadas = resumo.enviadas_por_usuario[ID_USUARIO]
    assert selecionadas[0].resultado.nota == 90
    assert selecionadas[0].resultado.avisos_objetivos == []


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
    pontuador = PontuadorFalso(notas)
    resumo = executar(
        ColetorFalso(vagas),
        ExtratorFalso(notas),
        notificador,
        repositorio,
        parametros(
            quantidade=quantidade,
            nota_minima=nota_minima,
            falhas_ate_pausar=falhas_ate_pausar,
        ),
        agora,
        pontuador,
    )
    enviadas = resumo.enviadas_por_usuario.get(ID_USUARIO, [])
    return [item.resultado for item in enviadas], notificador, pontuador


def test_envia_vagas_ordenadas_por_nota():
    selecionadas, notificador, _ = rodar([vaga(1), vaga(2), vaga(3)], {"1": 40, "2": 90, "3": 70})

    assert [resultado.vaga.id_externo for resultado in selecionadas] == ["2", "3", "1"]
    texto = notificador.textos[0]
    assert texto.index("Empresa 2") < texto.index("Empresa 3") < texto.index("Empresa 1")


def test_nao_envia_se_conta_sai_durante_a_coleta():
    repositorio = RepositorioFalso([usuario()])
    notificador = NotificadorFalso()

    class ColetorComSaida(ColetorFalso):
        def coletar(self):
            repositorio._usuarios.clear()
            return super().coletar()

    executar(
        ColetorComSaida([vaga(1)]),
        ExtratorFalso({"1": 90}),
        notificador,
        repositorio,
        parametros(),
        AGORA_DE_TESTE,
        PontuadorFalso({"1": 90}),
    )
    assert not notificador.textos
    assert not notificador.perguntas
    assert not repositorio.avaliacoes_gravadas
    assert not repositorio.envios_gravados


def test_nao_envia_para_chat_trocado_durante_a_avaliacao():
    class RepositorioComNovoChat(RepositorioFalso):
        def guardar_avaliacoes(self, usuario, avaliadas, modelo):
            super().guardar_avaliacoes(usuario, avaliadas, modelo)
            self._usuarios = [usuario.model_copy(update={"chat_id": "outro"})]

    repositorio = RepositorioComNovoChat([usuario()])
    selecionadas, notificador, _ = rodar([vaga(1)], {"1": 90}, repositorio=repositorio)
    assert not selecionadas
    assert not notificador.textos
    assert not repositorio.envios_gravados


def test_falha_na_revalidacao_impede_tambem_aviso_sem_vagas():
    class RepositorioIndisponivel(RepositorioFalso):
        def pode_entregar(self, usuario):
            raise ErroDeArmazenamento("banco indisponível")

    _, notificador, _ = rodar([], {}, repositorio=RepositorioIndisponivel([usuario()]))
    assert not notificador.textos
    assert not notificador.perguntas


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


def test_todas_abaixo_da_nota_minima_avisam_que_a_busca_continua():
    selecionadas, notificador, _ = rodar([vaga(1), vaga(2)], {"1": 35, "2": 20}, nota_minima=60)

    assert selecionadas == []
    assert "Nenhuma vaga nova compatível" in notificador.textos[0]
    assert "volta a procurar amanhã" in notificador.textos[0]


def test_vaga_sem_resultado_do_pontuador_fica_fora_da_mensagem():
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

    selecionadas, notificador, pontuador = rodar([da_adzuna, da_gupy], {"1": 80, "2": 80})

    assert pontuador.pontuadas == ["1"]
    assert len(selecionadas) == 1
    assert notificador.textos[0].count("Empresa 1") == 1


def test_sem_vagas_avisa_que_a_busca_continua_amanha():
    selecionadas, notificador, _ = rodar([], {})

    assert selecionadas == []
    assert "volta a procurar amanhã" in notificador.textos[0]


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
        ExtratorFalso({"1": 70}),
        notificador,
        repositorio,
        parametros(),
        AGORA_DE_TESTE,
        PontuadorFalso({"1": 70}),
    )

    assert notificador.chats == ["123", "456"]
    assert "Nenhuma vaga nova compatível" in notificador.textos[1]
    assert [item.resultado.nota for item in resumo.enviadas_por_usuario[ID_USUARIO]] == [70]
    assert ID_OUTRO_USUARIO not in resumo.enviadas_por_usuario
    assert resumo.usuarios == 2
    assert resumo.atendidos() == 1
    assert resumo.vagas_enviadas() == 1


def test_erro_no_telegram_de_um_usuario_nao_bloqueia_os_outros():
    repositorio = RepositorioFalso([usuario(chat_id="bloqueado"), usuario(ID_OUTRO_USUARIO)])
    notificador = NotificadorFalso(chats_com_erro={"bloqueado"})

    resumo = executar(
        ColetorFalso([vaga(1)]),
        ExtratorFalso({"1": 70}),
        notificador,
        repositorio,
        parametros(),
        AGORA_DE_TESTE,
        PontuadorFalso({"1": 70}),
    )

    assert notificador.chats == ["123"]
    assert list(resumo.enviadas_por_usuario) == [ID_OUTRO_USUARIO]
    assert [registro[0] for registro in repositorio.envios_gravados] == [ID_OUTRO_USUARIO]


def test_vaga_marcada_como_ja_vista_bloqueia_os_sosias():
    descricao = (
        "Dar apoio ao time de desenvolvimento nas rotinas do site, com estudo de "
        "requisitos, ajustes de paginas, testes manuais, correcao de defeitos simples "
        "e acompanhamento das entregas semanais junto ao coordenador da area."
    )
    recusada = vaga(1).model_copy(update={"descricao": descricao})
    sosia = vaga(2).model_copy(
        update={"titulo": recusada.titulo + " - Vaga", "descricao": descricao}
    )
    repositorio = RepositorioFalso(
        [usuario()], recusas=RecusasDoUsuario(vagas_repetidas=[recusada])
    )

    selecionadas, _, _ = rodar([sosia], {"2": 90}, repositorio=repositorio)

    assert selecionadas == []


def test_areas_recusadas_chegam_ao_pontuador():
    capturados = []

    def pontuador_espiao(vagas, extracoes, perfil):
        capturados.append(perfil.areas_recusadas)
        return []

    repositorio = RepositorioFalso(
        [usuario()], recusas=RecusasDoUsuario(areas=[AreaDeInteresse.DADOS_IA])
    )
    executar(
        ColetorFalso([vaga(1)]),
        ExtratorFalso({"1": 90}),
        NotificadorFalso(),
        repositorio,
        parametros(),
        AGORA_DE_TESTE,
        pontuador_espiao,
    )

    assert capturados == [[AreaDeInteresse.DADOS_IA]]


def test_republicacao_de_vaga_ja_enviada_em_outro_dia_nao_e_reenviada():
    descricao = (
        "Dar apoio ao time de desenvolvimento nas rotinas do site, com estudo de "
        "requisitos, ajustes de paginas, testes manuais, correcao de defeitos simples "
        "e acompanhamento das entregas semanais junto ao coordenador da area."
    )
    enviada = vaga(1).model_copy(update={"descricao": descricao})
    republicada = vaga(2).model_copy(
        update={"titulo": enviada.titulo + " - Vaga", "descricao": descricao}
    )
    repositorio = RepositorioFalso([usuario()], enviadas_recentes=[enviada])

    selecionadas, notificador, _ = rodar([republicada], {"2": 90}, repositorio=repositorio)

    assert selecionadas == []


def test_vaga_ja_enviada_nao_e_reavaliada_nem_repetida():
    repositorio = RepositorioFalso([usuario()], enviadas={("adzuna", "1")})

    selecionadas, notificador, pontuador = rodar(
        [vaga(1), vaga(2)], {"1": 90, "2": 60}, repositorio=repositorio
    )

    assert pontuador.pontuadas == ["2"]
    assert [resultado.vaga.id_externo for resultado in selecionadas] == ["2"]
    assert "Empresa 1" not in notificador.textos[0]


def test_apenas_o_perfil_informado_e_atendido():
    primeiro = usuario()
    segundo = usuario(id_usuario=UUID(int=2), chat_id="456")
    notificador = NotificadorFalso()
    repositorio = RepositorioFalso([primeiro, segundo])

    resumo = executar(
        ColetorFalso([vaga(1)]),
        ExtratorFalso({"1": 90}),
        notificador,
        repositorio,
        parametros(),
        AGORA_DE_TESTE,
        PontuadorFalso({"1": 90}),
        apenas_o_perfil=segundo.id,
    )

    assert set(resumo.enviadas_por_usuario) == {segundo.id}
    assert notificador.chats == ["456"]


def test_perfil_inexistente_nao_atende_ninguem():
    notificador = NotificadorFalso()
    repositorio = RepositorioFalso([usuario()])

    resumo = executar(
        ColetorFalso([vaga(1)]),
        ExtratorFalso({"1": 90}),
        notificador,
        repositorio,
        parametros(),
        AGORA_DE_TESTE,
        PontuadorFalso({"1": 90}),
        apenas_o_perfil=UUID(int=99),
    )

    assert resumo.enviadas_por_usuario == {}
    assert notificador.chats == []


def test_avaliacao_toda_bloqueada_nao_manda_mensagem_enganosa():
    selecionadas, notificador, _ = rodar([vaga(1), vaga(2)], {})

    assert selecionadas == []
    assert notificador.textos == []


def test_vaga_com_nota_guardada_nao_e_pontuada_de_novo():
    guardada = ResultadoMatch(vaga=vaga(1), nota=95, pontos_a_favor=["Guardado"])
    repositorio = RepositorioFalso([usuario()], guardadas=[guardada])

    selecionadas, notificador, pontuador = rodar(
        [vaga(1), vaga(2)], {"1": 10, "2": 60}, repositorio=repositorio
    )

    assert pontuador.pontuadas == ["2"]
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

    selecionadas, notificador, pontuador = rodar([sem_modalidade], {}, repositorio=repositorio)

    assert pontuador.pontuadas == []
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


def test_silencio_prolongado_acrescenta_a_sugestao_a_mensagem_do_dia():
    repositorio = RepositorioFalso([usuario(dias_sem_recomendacao=8)])

    selecionadas, notificador, _ = rodar([], {}, repositorio=repositorio)

    assert selecionadas == []
    assert "volta a procurar amanhã" in notificador.textos[0]
    assert "Já são 8 dias sem nenhuma recomendação" in notificador.textos[0]
    assert "remoto ou híbrido" in notificador.textos[0]
    assert repositorio.avisos_de_silencio == [ID_USUARIO]


def test_sugestao_por_silencio_nao_se_repete_todo_dia():
    repositorio = RepositorioFalso([usuario(dias_sem_recomendacao=20, dias_desde_o_aviso=2)])

    _, notificador, _ = rodar([], {}, repositorio=repositorio)

    assert "volta a procurar amanhã" in notificador.textos[0]
    assert "sem nenhuma recomendação" not in notificador.textos[0]
    assert repositorio.avisos_de_silencio == []


def test_usuario_recente_recebe_a_mensagem_do_dia_sem_a_sugestao():
    repositorio = RepositorioFalso([usuario(dias_sem_recomendacao=2)])

    _, notificador, _ = rodar([], {}, repositorio=repositorio)

    assert "volta a procurar amanhã" in notificador.textos[0]
    assert "sem nenhuma recomendação" not in notificador.textos[0]
    assert repositorio.avisos_de_silencio == []


def executar_com(repositorio: RepositorioFalso, vagas: list[Vaga], notas: dict[str, int]):
    extrator = ExtratorFalso(notas)
    executar(
        ColetorFalso(vagas),
        extrator,
        NotificadorFalso(),
        repositorio,
        parametros(),
        AGORA_DE_TESTE,
        PontuadorFalso(notas),
    )
    return extrator


def test_dobrar_os_usuarios_nao_dobra_as_vagas_extraidas():
    vagas = [vaga(1), vaga(2), vaga(3)]
    notas = {"1": 70, "2": 80, "3": 90}

    um = executar_com(RepositorioFalso([usuario()]), vagas, notas)
    dois = executar_com(
        RepositorioFalso([usuario(), usuario(ID_OUTRO_USUARIO, chat_id="456")]), vagas, notas
    )

    assert um.extraidas == ["1", "2", "3"]
    assert dois.extraidas == um.extraidas


def test_extracao_ja_guardada_nao_volta_ao_extrator():
    repositorio = RepositorioFalso([usuario()])
    repositorio.extracoes_guardadas["1"] = ExtracaoDaVaga(
        id_vaga="1", area_de_tecnologia=NivelCompatibilidade.COMPATIVEL
    )

    extrator = executar_com(repositorio, [vaga(1), vaga(2)], {"1": 70, "2": 80})

    assert extrator.extraidas == ["2"]


def test_extracao_nova_e_gravada_uma_vez_por_vaga():
    repositorio = RepositorioFalso([usuario(), usuario(ID_OUTRO_USUARIO, chat_id="456")])

    executar_com(repositorio, [vaga(1), vaga(2)], {"1": 70, "2": 80})

    assert sorted(repositorio.extracoes_guardadas) == ["1", "2"]
    assert repositorio.gravacoes_de_extracao == 1


def test_vaga_reprovada_no_prefiltro_de_todos_os_perfis_nao_e_extraida():
    fora_da_area = vaga(2, titulo="Estágio em Marketing Digital")

    extrator = executar_com(RepositorioFalso([usuario()]), [vaga(1), fora_da_area], {"1": 70})

    assert extrator.extraidas == ["1"]


def test_link_da_mensagem_usa_o_token_gravado_no_envio():
    repositorio = RepositorioFalso([usuario()])
    notificador = NotificadorFalso()

    executar(
        ColetorFalso([vaga(1)]),
        ExtratorFalso({"1": 70}),
        notificador,
        repositorio,
        parametros(url_de_rastreio=URL_DE_RASTREIO),
        AGORA_DE_TESTE,
        PontuadorFalso({"1": 70}),
    )

    assert len(repositorio.tokens_gravados) == 1
    assert f"{URL_DE_RASTREIO}?t={repositorio.tokens_gravados[0]}" in notificador.textos[0]


def test_cada_usuario_recebe_um_token_diferente_para_a_mesma_vaga():
    repositorio = RepositorioFalso([usuario(), usuario(ID_OUTRO_USUARIO, chat_id="456")])

    executar(
        ColetorFalso([vaga(1)]),
        ExtratorFalso({"1": 70}),
        NotificadorFalso(),
        repositorio,
        parametros(url_de_rastreio=URL_DE_RASTREIO),
        AGORA_DE_TESTE,
        PontuadorFalso({"1": 70}),
    )

    assert len(set(repositorio.tokens_gravados)) == 2


def test_a_execucao_apaga_as_contas_que_venceram_a_carencia():
    repositorio = RepositorioFalso([usuario()])

    executar_com(repositorio, [vaga(1)], {"1": 70})

    assert repositorio.carencias_aplicadas == [60]


def test_resumo_conta_falha_de_revalidacao_sem_interromper_outros_usuarios():
    class RepositorioComFalhaParcial(RepositorioFalso):
        def pode_entregar(self, destinatario):
            if destinatario.id == ID_USUARIO:
                raise ErroDeArmazenamento("indisponível")
            return super().pode_entregar(destinatario)

    repositorio = RepositorioComFalhaParcial([usuario(), usuario(ID_OUTRO_USUARIO, "456")])
    resumo = executar(
        ColetorFalso([vaga(1)]),
        ExtratorFalso({"1": 90}),
        NotificadorFalso(),
        repositorio,
        parametros(),
        AGORA_DE_TESTE,
        PontuadorFalso({"1": 90}),
    )
    assert resumo.usuarios_com_falha_de_revalidacao == 1
    assert resumo.usuarios_sem_entrega_por_falha_de_revalidacao == 1
    assert resumo.atendidos() == 1
    assert ID_OUTRO_USUARIO in resumo.enviadas_por_usuario


def test_falha_apos_entrega_nao_apaga_sucesso_do_resumo():
    class RepositorioComFalhaNoFeedback(RepositorioFalso):
        consultas = 0

        def pode_entregar(self, destinatario):
            self.consultas += 1
            if self.consultas == 3:
                raise ErroDeArmazenamento("indisponível")
            return True

    notificador = NotificadorFalso()
    resumo = executar(
        ColetorFalso([vaga(1)]),
        ExtratorFalso({"1": 90}),
        notificador,
        RepositorioComFalhaNoFeedback([usuario()]),
        parametros(),
        AGORA_DE_TESTE,
        PontuadorFalso({"1": 90}),
    )
    assert resumo.usuarios_com_falha_de_revalidacao == 1
    assert resumo.usuarios_sem_entrega_por_falha_de_revalidacao == 0
    assert resumo.atendidos() == 1
    assert not notificador.perguntas
