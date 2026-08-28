import logging
from datetime import date
from uuid import UUID

from radar.domain.models import ResultadoMatch, Usuario, Vaga
from radar.domain.ports import AvaliadorDeVagas, ColetorDeVagas, Notificador, Repositorio
from radar.filtering.duplicatas import remover_duplicatas
from radar.filtering.prefiltro import filtrar
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
            usuario, unicas, avaliador, notificador, repositorio, modelo, quantidade, data
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
    data: date,
) -> list[ResultadoMatch] | None:
    ja_enviadas = repositorio.ids_ja_enviadas(usuario)
    candidatas = [
        vaga
        for vaga in filtrar(vagas, usuario.perfil)
        if (vaga.fonte, vaga.id_externo) not in ja_enviadas
    ]
    guardadas = repositorio.avaliacoes_existentes(usuario, candidatas)
    ids_guardados = {resultado.vaga.id_externo for resultado in guardadas}
    pendentes = [vaga for vaga in candidatas if vaga.id_externo not in ids_guardados]
    novas = avaliador.avaliar(pendentes, usuario.perfil)
    selecionadas = ranquear(guardadas + novas)[:quantidade]
    logger.info(
        "usuário %s: %d candidatas, %d com nota guardada, %d avaliadas agora, %d enviadas",
        usuario.id,
        len(candidatas),
        len(guardadas),
        len(novas),
        len(selecionadas),
    )
    try:
        notificador.enviar(usuario.chat_id, formatar_mensagem(selecionadas, data))
    except ErroDeNotificacao as erro:
        logger.warning("usuário %s ficou sem mensagem: %s", usuario.id, erro)
        return None
    try:
        repositorio.registrar(usuario, novas, selecionadas, modelo)
    except ErroDeArmazenamento as erro:
        logger.warning("usuário %s: mensagem enviada, mas nada foi gravado: %s", usuario.id, erro)
    return selecionadas


def ranquear(resultados: list[ResultadoMatch]) -> list[ResultadoMatch]:
    return sorted(resultados, key=lambda resultado: resultado.nota, reverse=True)
