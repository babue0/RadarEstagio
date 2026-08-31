import time
from collections.abc import Callable, Iterable

import httpx

from radar.collectors.tentativas import requisitar_com_tentativas
from radar.domain.models import Vaga
from radar.settings import Settings

URL_BUSCA = "https://api.adzuna.com/v1/api/jobs/br/search"
FONTE = "adzuna"
EMPRESA_NAO_INFORMADA = "Empresa não informada"
LOCALIZACAO_PADRAO = "Brasil"
TERMO_OBRIGATORIO = "estágio"
TERMOS_DA_AREA = (
    "desenvolvimento software TI dados sistemas programação computação informática tecnologia"
)
RESULTADOS_POR_PAGINA = 50
LIMITE_DE_PAGINAS_POR_REGIAO = 4
POSICAO_DO_ESTADO = 2
POSICAO_DA_CIDADE = 3
TAMANHO_DO_RESUMO_DA_API = 500


class ColetorAdzuna:
    def __init__(
        self,
        settings: Settings,
        cliente_http: httpx.Client,
        cidades: Iterable[str] = (),
        esperar: Callable[[float], None] = time.sleep,
    ) -> None:
        self._settings = settings
        self._cliente_http = cliente_http
        self._cidades = tuple(cidades)
        self._esperar = esperar

    def coletar(self) -> list[Vaga]:
        vagas_por_id: dict[str, Vaga] = {}
        for cidade in (None, *self._cidades):
            for item in self._buscar_regiao(cidade):
                vaga = converter_em_vaga(item)
                vagas_por_id.setdefault(vaga.id_externo, vaga)
        return list(vagas_por_id.values())

    def _buscar_regiao(self, cidade: str | None) -> list[dict]:
        itens: list[dict] = []
        for pagina in range(1, LIMITE_DE_PAGINAS_POR_REGIAO + 1):
            resultados = self._buscar_pagina(pagina, cidade)
            itens.extend(resultados)
            if len(resultados) < RESULTADOS_POR_PAGINA:
                break
        return itens

    def _buscar_pagina(self, pagina: int, cidade: str | None) -> list[dict]:
        resposta = requisitar_com_tentativas(
            "Adzuna",
            lambda: self._cliente_http.get(
                f"{URL_BUSCA}/{pagina}", params=self._parametros_da_busca(cidade)
            ),
            self._esperar,
        )
        return resposta.json()["results"]

    def _parametros_da_busca(self, cidade: str | None) -> dict[str, str | int]:
        parametros: dict[str, str | int] = {
            "app_id": self._settings.adzuna_app_id,
            "app_key": self._settings.adzuna_app_key,
            "what_and": TERMO_OBRIGATORIO,
            "what_or": TERMOS_DA_AREA,
            "max_days_old": self._settings.dias_recentes,
            "results_per_page": RESULTADOS_POR_PAGINA,
            "content-type": "application/json",
        }
        if cidade:
            parametros["where"] = cidade
        return parametros


def nome_exibido(campo: dict | None, padrao: str) -> str:
    nome = (campo or {}).get("display_name")
    return nome.strip() if nome and nome.strip() else padrao


def formatar_localizacao(campo: dict | None) -> str:
    area = (campo or {}).get("area") or []
    if len(area) > POSICAO_DA_CIDADE:
        return f"{area[POSICAO_DA_CIDADE]}, {area[POSICAO_DO_ESTADO]}"
    return nome_exibido(campo, LOCALIZACAO_PADRAO)


def converter_em_vaga(item: dict) -> Vaga:
    descricao = item["description"]
    return Vaga(
        id_externo=str(item["id"]),
        fonte=FONTE,
        titulo=item["title"],
        empresa=nome_exibido(item.get("company"), EMPRESA_NAO_INFORMADA),
        localizacao=formatar_localizacao(item.get("location")),
        descricao=descricao,
        url=item["redirect_url"],
        publicada_em=item["created"],
        descricao_completa=not descricao_esta_truncada(descricao),
    )


def descricao_esta_truncada(descricao: str) -> bool:
    return len(descricao) >= TAMANHO_DO_RESUMO_DA_API or descricao.rstrip().endswith(("…", "..."))
