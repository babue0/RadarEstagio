import logging
from datetime import date
from uuid import UUID

from radar.domain.models import ResultadoMatch, Usuario, Vaga
from radar.domain.ports import AvaliadorDeVagas, ColetorDeVagas, Notificador, Repositorio
from radar.filtering.duplicatas import remover_duplicatas
from radar.filtering.prefiltro import filtrar
from radar.matching.regras import aplicar_regras_objetivas
from radar.notification.formatador import formatar_mensagem
from radar.notification.telegram import ErroDeNotificacao
from radar.storage.errors import ErroDeArmazenamento

logger = logging.getLogger(__name__)


def executar(
    coletor: ColetorDeVagas,
    avaliador: AvaliadorDeVagas,
    notificador: Notificador,
    repositorio: Repositorio,
    modelo: str,
    quantidade: int,
    nota_minima: int,
    falhas_ate_pausar: int,
    data: date,
) -> dict[UUID, list[ResultadoMatch]]:
    usuarios = repositorio.listar_ativos()
    coletadas = coletor.coletar()
    unicas = remover_duplicatas(coletadas)
    logger.info(
        "%d vagas coletadas, %d únicas, %d usuários", len(coletadas), len(unicas), len(usuarios)
    )
    enviadas_por_usuario: dict[UUID, list[ResultadoMatch]] = {}
    for usuario in usuarios:
        selecionadas = atender_usuario(
            usuario,
            unicas,
            avaliador,
            notificador,
            repositorio,
            modelo,
            quantidade,
            nota_minima,
            falhas_ate_pausar,
            data,
        )
        if selecionadas is not None:
            enviadas_por_usuario[usuario.id] = selecionadas
    return enviadas_por_usuario


def atender_usuario(
    usuario: Usuario,
    vagas: list[Vaga],
    avaliador: AvaliadorDeVagas,
    notificador: Notificador,
    repositorio: Repositorio,
    modelo: str,
    quantidade: int,
    nota_minima: int,
    falhas_ate_pausar: int,
    data: date,
) -> list[ResultadoMatch] | None:
    ja_enviadas = repositorio.ids_ja_enviadas(usuario)
    candidatas = [
        vaga
        for vaga in filtrar(vagas, usuario.perfil)
        if (vaga.fonte, vaga.id_externo) not in ja_enviadas
    ]
    guardadas = aplicar_regras_objetivas(
        repositorio.avaliacoes_existentes(usuario, candidatas), usuario.perfil
    )
    ids_guardados = {resultado.vaga.id_externo for resultado in guardadas}
    pendentes = [vaga for vaga in candidatas if vaga.id_externo not in ids_guardados]
    novas = aplicar_regras_objetivas(avaliador.avaliar(pendentes, usuario.perfil), usuario.perfil)
    if pendentes and not novas and not guardadas:
        logger.warning(
            "usuário %s ficou sem mensagem: nenhuma das %d vagas pendentes pôde ser avaliada",
            usuario.id,
            len(pendentes),
        )
        return None
    selecionadas = selecionar(guardadas + novas, quantidade, nota_minima)
    logger.info(
        "usuário %s: %d candidatas, %d com nota guardada, %d avaliadas agora, %d enviadas",
        usuario.id,
        len(candidatas),
        len(guardadas),
        len(novas),
        len(selecionadas),
    )
    gravar_avaliacoes(repositorio, usuario, novas, modelo)
    try:
        notificador.enviar(usuario.chat_id, formatar_mensagem(selecionadas, data))
    except ErroDeNotificacao as erro:
        logger.warning("usuário %s ficou sem mensagem: %s", usuario.id, erro)
        pausar_apos_falhas_seguidas(repositorio, usuario, falhas_ate_pausar)
        return None
    try:
        repositorio.registrar_envios(usuario, selecionadas)
    except ErroDeArmazenamento as erro:
        logger.warning(
            "usuário %s: mensagem enviada, mas o envio não foi gravado: %s", usuario.id, erro
        )
    return selecionadas


def gravar_avaliacoes(
    repositorio: Repositorio, usuario: Usuario, novas: list[ResultadoMatch], modelo: str
) -> None:
    try:
        repositorio.guardar_avaliacoes(usuario, novas, modelo)
    except ErroDeArmazenamento as erro:
        logger.warning("usuário %s: avaliações não foram gravadas: %s", usuario.id, erro)


def pausar_apos_falhas_seguidas(
    repositorio: Repositorio, usuario: Usuario, falhas_ate_pausar: int
) -> None:
    try:
        falhas = repositorio.registrar_falha_de_envio(usuario)
        if falhas < falhas_ate_pausar:
            return
        repositorio.pausar(usuario)
    except ErroDeArmazenamento as erro:
        logger.warning("usuário %s: falha de envio não registrada: %s", usuario.id, erro)
        return
    logger.warning("usuário %s pausado após %d falhas seguidas de envio", usuario.id, falhas)


def selecionar(
    resultados: list[ResultadoMatch], quantidade: int, nota_minima: int
) -> list[ResultadoMatch]:
    aprovados = [resultado for resultado in resultados if resultado.nota >= nota_minima]
    return ranquear(aprovados)[:quantidade]


def ranquear(resultados: list[ResultadoMatch]) -> list[ResultadoMatch]:
    return sorted(resultados, key=lambda resultado: resultado.nota, reverse=True)
