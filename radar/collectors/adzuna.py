import httpx

from radar.collectors.errors import ErroDeColeta
from radar.domain.models import Vaga
from radar.settings import Settings

URL_BUSCA = "https://api.adzuna.com/v1/api/jobs/br/search/1"
FONTE = "adzuna"
TERMO_DE_BUSCA = "estágio"
CATEGORIA_TECNOLOGIA = "it-jobs"
RESULTADOS_POR_PAGINA = 50


class ColetorAdzuna:
    def __init__(self, settings: Settings, cliente_http: httpx.Client) -> None:
        self._settings = settings
        self._cliente_http = cliente_http

    def coletar(self) -> list[Vaga]:
        try:
            resposta = self._cliente_http.get(URL_BUSCA, params=self._parametros_da_busca())
            resposta.raise_for_status()
        except httpx.HTTPStatusError as erro:
            status = erro.response.status_code
            raise ErroDeColeta(f"Adzuna respondeu HTTP {status} ao buscar vagas") from None
        except httpx.HTTPError as erro:
            raise ErroDeColeta(
                f"Falha de rede ao buscar vagas na Adzuna ({type(erro).__name__})"
            ) from erro
        return [converter_em_vaga(item) for item in resposta.json()["results"]]

    def _parametros_da_busca(self) -> dict[str, str | int]:
        return {
            "app_id": self._settings.adzuna_app_id,
            "app_key": self._settings.adzuna_app_key,
            "what": TERMO_DE_BUSCA,
            "category": CATEGORIA_TECNOLOGIA,
            "max_days_old": self._settings.adzuna_dias_recentes,
            "results_per_page": RESULTADOS_POR_PAGINA,
            "content-type": "application/json",
        }


def converter_em_vaga(item: dict) -> Vaga:
    return Vaga(
        id_externo=str(item["id"]),
        fonte=FONTE,
        titulo=item["title"],
        empresa=item["company"]["display_name"],
        localizacao=item["location"]["display_name"],
        descricao=item["description"],
        url=item["redirect_url"],
        publicada_em=item["created"],
    )
