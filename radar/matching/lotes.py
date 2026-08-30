import logging
import time
from collections.abc import Callable

from radar.domain.models import Perfil, ResultadoMatch, Vaga
from radar.domain.ports import AvaliadorDeVagas
from radar.matching.errors import CotaDeAvaliacaoExcedida, ErroDeAvaliacao

logger = logging.getLogger(__name__)

ESPERA_PADRAO_EM_SEGUNDOS = 60
ESPERA_MAXIMA_EM_SEGUNDOS = 120
MARGEM_DE_ESPERA_EM_SEGUNDOS = 1
TENTATIVAS_APOS_COTA_EXCEDIDA = 3


class AvaliadorEmLotes:
    def __init__(
        self,
        avaliador: AvaliadorDeVagas,
        tamanho_do_lote: int,
        esperar: Callable[[float], None] = time.sleep,
    ) -> None:
        if tamanho_do_lote < 1:
            raise ValueError("tamanho_do_lote deve ser pelo menos 1")
        self._avaliador = avaliador
        self._tamanho_do_lote = tamanho_do_lote
        self._esperar = esperar

    def avaliar(self, vagas: list[Vaga], perfil: Perfil) -> list[ResultadoMatch]:
        resultados: list[ResultadoMatch] = []
        for inicio in range(0, len(vagas), self._tamanho_do_lote):
            lote = vagas[inicio : inicio + self._tamanho_do_lote]
            try:
                resultados.extend(self._avaliar_respeitando_a_cota(lote, perfil))
            except CotaDeAvaliacaoExcedida as erro:
                logger.warning(
                    "Cota excedida; %d de %d vagas ficaram sem avaliação: %s",
                    len(vagas) - len(resultados),
                    len(vagas),
                    erro,
                )
                break
        return resultados

    def _avaliar_respeitando_a_cota(self, lote: list[Vaga], perfil: Perfil) -> list[ResultadoMatch]:
        for tentativa in range(1, TENTATIVAS_APOS_COTA_EXCEDIDA + 1):
            try:
                return self._avaliar_com_tolerancia(lote, perfil)
            except CotaDeAvaliacaoExcedida as erro:
                espera = erro.aguardar_segundos or ESPERA_PADRAO_EM_SEGUNDOS
                if espera > ESPERA_MAXIMA_EM_SEGUNDOS:
                    raise
                logger.info(
                    "Cota por minuto atingida; aguardando %.0f s (tentativa %d de %d)",
                    espera,
                    tentativa,
                    TENTATIVAS_APOS_COTA_EXCEDIDA,
                )
                self._esperar(espera + MARGEM_DE_ESPERA_EM_SEGUNDOS)
        return self._avaliar_com_tolerancia(lote, perfil)

    def _avaliar_com_tolerancia(self, lote: list[Vaga], perfil: Perfil) -> list[ResultadoMatch]:
        try:
            resultados = self._avaliador.avaliar(lote, perfil)
        except CotaDeAvaliacaoExcedida:
            raise
        except ErroDeAvaliacao as erro:
            return self._dividir_e_tentar_de_novo(lote, perfil, erro)
        faltantes = vagas_sem_resultado(lote, resultados)
        if faltantes and len(lote) > 1:
            logger.info("%d vagas sem avaliação no lote; reavaliando uma a uma", len(faltantes))
            for vaga in faltantes:
                resultados.extend(self._avaliar_com_tolerancia([vaga], perfil))
        elif faltantes:
            logger.warning("Vaga %s ignorada: avaliador não a devolveu", lote[0].id_externo)
        return resultados

    def _dividir_e_tentar_de_novo(
        self, lote: list[Vaga], perfil: Perfil, erro: ErroDeAvaliacao
    ) -> list[ResultadoMatch]:
        if len(lote) == 1:
            logger.warning("Vaga %s ignorada: %s", lote[0].id_externo, erro)
            return []
        metade = len(lote) // 2
        logger.info("Lote de %d vagas falhou (%s); dividindo em dois", len(lote), erro)
        return self._avaliar_com_tolerancia(lote[:metade], perfil) + self._avaliar_com_tolerancia(
            lote[metade:], perfil
        )


def vagas_sem_resultado(vagas: list[Vaga], resultados: list[ResultadoMatch]) -> list[Vaga]:
    avaliadas = {resultado.vaga.id_externo for resultado in resultados}
    return [vaga for vaga in vagas if vaga.id_externo not in avaliadas]
