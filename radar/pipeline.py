import logging
from datetime import date

from radar.domain.models import Perfil, ResultadoMatch
from radar.domain.ports import AvaliadorDeVagas, ColetorDeVagas, Notificador
from radar.filtering.prefiltro import filtrar
from radar.notification.formatador import formatar_mensagem

logger = logging.getLogger(__name__)


def executar(
    coletor: ColetorDeVagas,
    avaliador: AvaliadorDeVagas,
    notificador: Notificador,
    perfil: Perfil,
    quantidade: int,
    data: date,
) -> list[ResultadoMatch]:
    coletadas = coletor.coletar()
    candidatas = filtrar(coletadas, perfil)
    logger.info("%d vagas coletadas, %d após o pré-filtro", len(coletadas), len(candidatas))
    resultados = avaliador.avaliar(candidatas, perfil)
    logger.info("%d de %d vagas avaliadas", len(resultados), len(candidatas))
    selecionadas = ranquear(resultados)[:quantidade]
    notificador.enviar(formatar_mensagem(selecionadas, data))
    logger.info("%d vagas enviadas", len(selecionadas))
    return selecionadas


def ranquear(resultados: list[ResultadoMatch]) -> list[ResultadoMatch]:
    return sorted(resultados, key=lambda resultado: resultado.nota, reverse=True)
