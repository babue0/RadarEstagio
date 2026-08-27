import re

from radar.domain.models import Vaga
from radar.filtering.prefiltro import normalizar

PADRAO_NAO_ALFANUMERICO = re.compile(r"[^a-z0-9]+")


def chave_de_duplicata(vaga: Vaga) -> str:
    return PADRAO_NAO_ALFANUMERICO.sub(" ", normalizar(f"{vaga.titulo} {vaga.empresa}")).strip()


def mais_completa(primeira: Vaga, segunda: Vaga) -> Vaga:
    informa_modalidade = (primeira.modalidade is not None, segunda.modalidade is not None)
    if informa_modalidade == (False, True):
        return segunda
    if informa_modalidade == (True, False):
        return primeira
    return segunda if len(segunda.descricao) > len(primeira.descricao) else primeira


def remover_duplicatas(vagas: list[Vaga]) -> list[Vaga]:
    escolhidas: dict[str, Vaga] = {}
    for vaga in vagas:
        chave = chave_de_duplicata(vaga)
        escolhidas[chave] = mais_completa(escolhidas[chave], vaga) if chave in escolhidas else vaga
    return list(escolhidas.values())
