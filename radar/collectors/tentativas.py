import logging
import time
from collections.abc import Callable

import httpx

from radar.collectors.errors import ErroDeColeta

logger = logging.getLogger(__name__)

TENTATIVAS_POR_REQUISICAO = 3
ESPERAS_ENTRE_TENTATIVAS_EM_SEGUNDOS = (2, 10)
STATUS_QUE_VALEM_NOVA_TENTATIVA = frozenset({429, 500, 502, 503, 504})


def requisitar_com_tentativas(
    fonte: str,
    requisitar: Callable[[], httpx.Response],
    esperar: Callable[[float], None] = time.sleep,
) -> httpx.Response:
    for tentativa in range(1, TENTATIVAS_POR_REQUISICAO + 1):
        ultima = tentativa == TENTATIVAS_POR_REQUISICAO
        try:
            resposta = requisitar()
            resposta.raise_for_status()
            return resposta
        except httpx.HTTPStatusError as erro:
            status = erro.response.status_code
            if ultima or status not in STATUS_QUE_VALEM_NOVA_TENTATIVA:
                raise ErroDeColeta(f"{fonte} respondeu HTTP {status} ao buscar vagas") from None
        except httpx.HTTPError as erro:
            if ultima:
                raise ErroDeColeta(
                    f"Falha de rede ao buscar vagas na {fonte} ({type(erro).__name__})"
                ) from erro
        espera = ESPERAS_ENTRE_TENTATIVAS_EM_SEGUNDOS[tentativa - 1]
        logger.info("%s indisponível; nova tentativa em %d s", fonte, espera)
        esperar(espera)
    raise ErroDeColeta(f"{fonte} não respondeu após {TENTATIVAS_POR_REQUISICAO} tentativas")
