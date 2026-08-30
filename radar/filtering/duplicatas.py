import re

from radar.domain.models import Vaga
from radar.filtering.prefiltro import cidade, normalizar

PADRAO_NAO_ALFANUMERICO = re.compile(r"[^a-z0-9]+")
PADRAO_SUFIXO_DE_AGREGADOR = re.compile(r"\s*-\s*(?:vaga(?: aberta)?|recrutamento aberto)\s*$")
SEMELHANCA_MINIMA_ENTRE_DESCRICOES = 0.8
MINIMO_DE_PALAVRAS_PARA_COMPARAR = 20
PALAVRAS_COMPARADAS_DA_DESCRICAO = 40


def chave_de_duplicata(vaga: Vaga) -> str:
    return limpar(f"{vaga.titulo} {vaga.empresa}")


def chave_de_anuncio(vaga: Vaga) -> str:
    titulo = PADRAO_SUFIXO_DE_AGREGADOR.sub("", normalizar(vaga.titulo))
    return limpar(f"{titulo} {cidade(vaga.localizacao)}")


def limpar(texto: str) -> str:
    return PADRAO_NAO_ALFANUMERICO.sub(" ", normalizar(texto)).strip()


def palavras_iniciais(texto: str) -> set[str]:
    return set(limpar(texto).split()[:PALAVRAS_COMPARADAS_DA_DESCRICAO])


def descricoes_semelhantes(primeira: Vaga, segunda: Vaga) -> bool:
    palavras_primeira = palavras_iniciais(primeira.descricao)
    palavras_segunda = palavras_iniciais(segunda.descricao)
    if min(len(palavras_primeira), len(palavras_segunda)) < MINIMO_DE_PALAVRAS_PARA_COMPARAR:
        return False
    em_comum = len(palavras_primeira & palavras_segunda)
    total = len(palavras_primeira | palavras_segunda)
    return em_comum / total >= SEMELHANCA_MINIMA_ENTRE_DESCRICOES


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
    return remover_republicacoes(list(escolhidas.values()))


def remover_republicacoes(vagas: list[Vaga]) -> list[Vaga]:
    escolhidas: list[Vaga] = []
    posicoes_por_anuncio: dict[str, list[int]] = {}
    for vaga in vagas:
        posicoes = posicoes_por_anuncio.setdefault(chave_de_anuncio(vaga), [])
        repetida = next(
            (posicao for posicao in posicoes if descricoes_semelhantes(escolhidas[posicao], vaga)),
            None,
        )
        if repetida is None:
            posicoes.append(len(escolhidas))
            escolhidas.append(vaga)
        else:
            escolhidas[repetida] = mais_completa(escolhidas[repetida], vaga)
    return escolhidas
