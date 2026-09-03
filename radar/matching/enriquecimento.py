import logging
from html.parser import HTMLParser

import httpx

from radar.domain.models import ExtracaoDaVaga, Vaga
from radar.domain.ports import ExtratorDeVagas

logger = logging.getLogger(__name__)

FONTE_ADZUNA = "adzuna"
CLASSE_DA_DESCRICAO = "adp-body"
TAGS_DE_QUEBRA = frozenset({"br", "div", "li", "p"})
TAGS_SEM_FECHAMENTO = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "source",
        "track",
        "wbr",
    }
)


class ExtratorComDescricoesCompletas:
    def __init__(self, extrator: ExtratorDeVagas, cliente_http: httpx.Client) -> None:
        self._extrator = extrator
        self._cliente_http = cliente_http
        self._cache: dict[tuple[str, str], Vaga] = {}

    def extrair(self, vagas: list[Vaga]) -> list[ExtracaoDaVaga]:
        enriquecidas = [self._enriquecer(vaga) for vaga in vagas]
        return self._extrator.extrair(enriquecidas)

    def _enriquecer(self, vaga: Vaga) -> Vaga:
        if not descricao_parece_truncada(vaga):
            return vaga
        chave = (vaga.fonte, vaga.id_externo)
        if chave in self._cache:
            return self._cache[chave]
        enriquecida = buscar_descricao_completa(vaga, self._cliente_http)
        self._cache[chave] = enriquecida
        return enriquecida


def descricao_parece_truncada(vaga: Vaga) -> bool:
    return vaga.fonte == FONTE_ADZUNA and not vaga.descricao_completa


def buscar_descricao_completa(vaga: Vaga, cliente_http: httpx.Client) -> Vaga:
    try:
        resposta = cliente_http.get(vaga.url, follow_redirects=True)
        resposta.raise_for_status()
    except httpx.HTTPError as erro:
        logger.warning(
            "Não foi possível completar a descrição da vaga %s da Adzuna: %s",
            vaga.id_externo,
            type(erro).__name__,
        )
        return vaga
    descricao = extrair_descricao_da_pagina(resposta.text)
    if not descricao:
        logger.warning("Página da vaga %s da Adzuna não contém a descrição", vaga.id_externo)
        return vaga
    return vaga.model_copy(update={"descricao": descricao, "descricao_completa": True})


def extrair_descricao_da_pagina(pagina: str) -> str:
    extrator = ExtratorDaDescricao()
    extrator.feed(pagina)
    return " ".join("".join(extrator.partes).split())


class ExtratorDaDescricao(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.partes: list[str] = []
        self._profundidade = 0

    def handle_starttag(self, tag: str, atributos: list[tuple[str, str | None]]) -> None:
        classes = (dict(atributos).get("class") or "").split()
        if not self._profundidade and tag == "section" and CLASSE_DA_DESCRICAO in classes:
            self._profundidade = 1
            return
        if not self._profundidade:
            return
        if tag in TAGS_DE_QUEBRA:
            self.partes.append(" ")
        if tag not in TAGS_SEM_FECHAMENTO:
            self._profundidade += 1

    def handle_endtag(self, tag: str) -> None:
        if not self._profundidade or tag in TAGS_SEM_FECHAMENTO:
            return
        self._profundidade -= 1

    def handle_data(self, dados: str) -> None:
        if self._profundidade:
            self.partes.append(dados)
