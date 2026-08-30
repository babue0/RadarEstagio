import html
import re
from collections.abc import Iterable
from datetime import UTC, datetime

import httpx

from radar.collectors.errors import ErroDeColeta
from radar.domain.models import Modalidade, Vaga

URL_BUSCA = "https://employability-portal.gupy.io/api/v1/jobs"
FONTE = "gupy"
TIPO_ESTAGIO = "vacancy_type_internship"
RESULTADOS_POR_PAGINA = 100
LIMITE_DE_PAGINAS_POR_REGIAO = 10
LOCALIZACAO_PADRAO = "Brasil"
MODALIDADE_POR_WORKPLACE_TYPE = {
    "remote": Modalidade.REMOTO,
    "hybrid": Modalidade.HIBRIDO,
    "on-site": Modalidade.PRESENCIAL,
}
PADRAO_TAG_HTML = re.compile(r"<[^>]+>")
PADRAO_ESPACOS = re.compile(r"\s+")


class ColetorGupy:
    def __init__(
        self, cliente_http: httpx.Client, publicadas_desde: datetime, cidades: Iterable[str] = ()
    ) -> None:
        self._cliente_http = cliente_http
        self._publicadas_desde = publicadas_desde
        self._cidades = tuple(cidades)

    def coletar(self) -> list[Vaga]:
        vagas_por_id: dict[str, Vaga] = {}
        for cidade in (None, *self._cidades):
            for item in self._buscar_recentes(cidade):
                vaga = converter_em_vaga(item)
                vagas_por_id.setdefault(vaga.id_externo, vaga)
        return list(vagas_por_id.values())

    def _buscar_recentes(self, cidade: str | None) -> list[dict]:
        recentes: list[dict] = []
        for pagina in range(LIMITE_DE_PAGINAS_POR_REGIAO):
            itens = self._buscar_pagina(cidade, pagina * RESULTADOS_POR_PAGINA)
            recentes.extend(item for item in itens if self._e_recente(item))
            pagina_incompleta = len(itens) < RESULTADOS_POR_PAGINA
            if pagina_incompleta or not self._e_recente(itens[-1]):
                break
        return recentes

    def _buscar_pagina(self, cidade: str | None, offset: int) -> list[dict]:
        parametros: dict[str, str | int] = {
            "jobName": "",
            "type": TIPO_ESTAGIO,
            "limit": RESULTADOS_POR_PAGINA,
            "offset": offset,
        }
        if cidade:
            parametros["city"] = cidade
        try:
            resposta = self._cliente_http.get(URL_BUSCA, params=parametros)
            resposta.raise_for_status()
        except httpx.HTTPStatusError as erro:
            status = erro.response.status_code
            raise ErroDeColeta(f"Gupy respondeu HTTP {status} ao buscar vagas") from None
        except httpx.HTTPError as erro:
            raise ErroDeColeta(
                f"Falha de rede ao buscar vagas na Gupy ({type(erro).__name__})"
            ) from erro
        return resposta.json()["data"]

    def _e_recente(self, item: dict) -> bool:
        data = item.get("publishedDate")
        if not data:
            return False
        return interpretar_data_de_publicacao(data) >= self._publicadas_desde


def converter_em_vaga(item: dict) -> Vaga:
    return Vaga(
        id_externo=str(item["id"]),
        fonte=FONTE,
        titulo=item["name"].strip(),
        empresa=item["careerPageName"].strip(),
        localizacao=formatar_localizacao(item),
        descricao=limpar_html(item["description"]),
        url=item["jobUrl"],
        publicada_em=interpretar_data_de_publicacao(item["publishedDate"]),
        modalidade=MODALIDADE_POR_WORKPLACE_TYPE.get(item.get("workplaceType")),
    )


def interpretar_data_de_publicacao(texto: str) -> datetime:
    data = datetime.fromisoformat(texto)
    if data.tzinfo is None:
        return data.replace(tzinfo=UTC)
    return data


def formatar_localizacao(item: dict) -> str:
    partes = [parte.strip() for parte in (item.get("city"), item.get("state")) if parte]
    return ", ".join(partes) or LOCALIZACAO_PADRAO


def limpar_html(texto: str) -> str:
    sem_tags = PADRAO_TAG_HTML.sub(" ", texto)
    return PADRAO_ESPACOS.sub(" ", html.unescape(sem_tags)).strip()
