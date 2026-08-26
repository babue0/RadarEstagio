import logging
from datetime import date

from radar.domain.models import Perfil, ResultadoMatch, Vaga
from radar.domain.ports import AvaliadorDeVagas, ColetorDeVagas, Notificador
from radar.filtering.prefiltro import filtrar
from radar.matching.gemini import CotaDeAvaliacaoExcedida, ErroDeAvaliacao
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
    resultados = avaliar_todas(avaliador, candidatas, perfil)
    selecionadas = ranquear(resultados)[:quantidade]
    notificador.enviar(formatar_mensagem(selecionadas, data))
    logger.info("%d vagas enviadas", len(selecionadas))
    return selecionadas


def avaliar_todas(
    avaliador: AvaliadorDeVagas, vagas: list[Vaga], perfil: Perfil
) -> list[ResultadoMatch]:
    resultados = []
    for posicao, vaga in enumerate(vagas):
        try:
            resultados.append(avaliador.avaliar(vaga, perfil))
        except CotaDeAvaliacaoExcedida as erro:
            logger.warning(
                "Cota do Gemini excedida; %d de %d vagas ficaram sem avaliação: %s",
                len(vagas) - posicao,
                len(vagas),
                erro,
            )
            break
        except ErroDeAvaliacao as erro:
            logger.warning("Vaga %s ignorada: %s", vaga.id_externo, erro)
    return resultados


def ranquear(resultados: list[ResultadoMatch]) -> list[ResultadoMatch]:
    return sorted(resultados, key=lambda resultado: resultado.nota, reverse=True)
