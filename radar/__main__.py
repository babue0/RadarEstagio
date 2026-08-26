import argparse
import sys

import httpx
from google import genai
from pydantic import ValidationError

from radar.collectors.adzuna import ColetorAdzuna, ErroDeColeta
from radar.domain.perfil_fixo import perfil_do_mvp
from radar.filtering.prefiltro import filtrar
from radar.matching.gemini import AvaliadorGemini, ErroDeAvaliacao
from radar.settings import Settings

TIPOS_DE_ERRO_DE_PREENCHIMENTO = frozenset({"missing", "string_too_short"})
TIMEOUT_HTTP_EM_SEGUNDOS = 30
LIMITE_DE_VAGAS_NA_AVALIACAO_MANUAL = 3


def nomes_das_variaveis_nao_preenchidas(erro: ValidationError) -> list[str]:
    return [
        str(detalhe["loc"][0]).upper()
        for detalhe in erro.errors()
        if detalhe["type"] in TIPOS_DE_ERRO_DE_PREENCHIMENTO
    ]


def carregar_settings() -> Settings | None:
    try:
        return Settings()
    except ValidationError as erro:
        print("Variáveis de ambiente ausentes ou vazias:", file=sys.stderr)
        for nome in nomes_das_variaveis_nao_preenchidas(erro):
            print(f"  - {nome}", file=sys.stderr)
        return None


def verificar_configuracao(settings: Settings) -> None:
    print("Configuração carregada com sucesso.")
    print(f"Dias recentes na Adzuna: {settings.adzuna_dias_recentes}")
    print(f"Vagas enviadas por execução: {settings.quantidade_vagas_enviadas}")


def coletar(settings: Settings) -> None:
    with httpx.Client(timeout=TIMEOUT_HTTP_EM_SEGUNDOS) as cliente_http:
        vagas = ColetorAdzuna(settings, cliente_http).coletar()
    print(f"{len(vagas)} vagas coletadas na Adzuna")
    for vaga in vagas:
        print(f"- {vaga.titulo} | {vaga.empresa} | {vaga.localizacao}")
        print(f"  {vaga.url}")


def avaliar(settings: Settings) -> None:
    perfil = perfil_do_mvp()
    with httpx.Client(timeout=TIMEOUT_HTTP_EM_SEGUNDOS) as cliente_http:
        vagas = filtrar(ColetorAdzuna(settings, cliente_http).coletar(), perfil)
    avaliador = AvaliadorGemini(settings, genai.Client(api_key=settings.gemini_api_key))
    selecionadas = vagas[:LIMITE_DE_VAGAS_NA_AVALIACAO_MANUAL]
    print(f"{len(vagas)} vagas após o pré-filtro; avaliando {len(selecionadas)} com o Gemini")
    for vaga in selecionadas:
        resultado = avaliador.avaliar(vaga, perfil)
        print(f"- [{resultado.nota:3d}] {vaga.titulo} | {vaga.empresa} | {vaga.localizacao}")
        print(f"  Motivo: {resultado.motivo}")
        if resultado.alerta_pegadinha:
            print(f"  Alerta: {resultado.alerta_pegadinha}")


COMANDOS = {"coletar": coletar, "avaliar": avaliar}


def main() -> None:
    parser = argparse.ArgumentParser(prog="radar", description="Radar de Estágio")
    subcomandos = parser.add_subparsers(dest="comando")
    subcomandos.add_parser("coletar", help="busca vagas reais na Adzuna e imprime título e URL")
    subcomandos.add_parser("avaliar", help="coleta, pré-filtra e avalia algumas vagas com o Gemini")
    argumentos = parser.parse_args()

    settings = carregar_settings()
    if settings is None:
        sys.exit(1)

    executar = COMANDOS.get(argumentos.comando, verificar_configuracao)
    try:
        executar(settings)
    except (ErroDeColeta, ErroDeAvaliacao) as erro:
        print(erro, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
