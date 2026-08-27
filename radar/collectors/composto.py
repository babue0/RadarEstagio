import logging

from radar.collectors.errors import ErroDeColeta
from radar.domain.models import Vaga
from radar.domain.ports import ColetorDeVagas

logger = logging.getLogger(__name__)


class ColetorComposto:
    def __init__(self, coletores: dict[str, ColetorDeVagas]) -> None:
        if not coletores:
            raise ValueError("é necessário pelo menos um coletor")
        self._coletores = coletores

    def coletar(self) -> list[Vaga]:
        vagas: list[Vaga] = []
        falhas: list[str] = []
        for fonte, coletor in self._coletores.items():
            try:
                coletadas = coletor.coletar()
            except ErroDeColeta as erro:
                logger.warning("Fonte %s ignorada nesta execução: %s", fonte, erro)
                falhas.append(f"{fonte}: {erro}")
                continue
            logger.info("%d vagas coletadas em %s", len(coletadas), fonte)
            vagas.extend(coletadas)
        if len(falhas) == len(self._coletores):
            raise ErroDeColeta("Nenhuma fonte respondeu: " + "; ".join(falhas))
        return vagas
