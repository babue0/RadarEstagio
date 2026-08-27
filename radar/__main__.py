import argparse
import logging
import sys
from datetime import date

import httpx
from pydantic import ValidationError

from radar.collectors.adzuna import ColetorAdzuna, ErroDeColeta
from radar.domain.perfil_fixo import perfil_do_mvp
from radar.filtering.prefiltro import filtrar
from radar.matching.errors import ErroDeAvaliacao
from radar.matching.factory import criar_avaliador
from radar.matching.lotes import AvaliadorEmLotes
from radar.notification.telegram import ErroDeNotificacao, NotificadorTelegram
from radar.pipeline import executar
from radar.settings import Settings

TIPOS_DE_ERRO_DE_PREENCHIMENTO = frozenset({"missing", "string_too_short"})
TIMEOUT_HTTP_EM_SEGUNDOS = 30
LIMITE_DE_VAGAS_NA_AVALIACAO_MANUAL = 3
COMANDO_PADRAO = "rodar"


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
    print(f"Avaliador: {settings.avaliador}")
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
    selecionadas = vagas[:LIMITE_DE_VAGAS_NA_AVALIACAO_MANUAL]
    print(
        f"{len(vagas)} vagas após o pré-filtro; "
        f"avaliando {len(selecionadas)} com {settings.avaliador}"
    )
    for resultado in montar_avaliador(settings).avaliar(selecionadas, perfil):
        vaga = resultado.vaga
        print(f"- [{resultado.nota:3d}] {vaga.titulo} | {vaga.empresa} | {vaga.localizacao}")
        print(f"  Motivo: {resultado.motivo}")
        if resultado.alerta_pegadinha:
            print(f"  Alerta: {resultado.alerta_pegadinha}")


def testar_telegram(settings: Settings) -> None:
    with httpx.Client(timeout=TIMEOUT_HTTP_EM_SEGUNDOS) as cliente_http:
        NotificadorTelegram(settings, cliente_http).enviar("Radar OK")
    print(f"Mensagem enviada para o chat {settings.telegram_chat_id}")


def montar_avaliador(settings: Settings) -> AvaliadorEmLotes:
    return AvaliadorEmLotes(criar_avaliador(settings), settings.gemini_vagas_por_lote)


def rodar(settings: Settings) -> None:
    with httpx.Client(timeout=TIMEOUT_HTTP_EM_SEGUNDOS) as cliente_http:
        selecionadas = executar(
            ColetorAdzuna(settings, cliente_http),
            montar_avaliador(settings),
            NotificadorTelegram(settings, cliente_http),
            perfil_do_mvp(),
            settings.quantidade_vagas_enviadas,
            date.today(),
        )
    print(f"{len(selecionadas)} vagas enviadas para o chat {settings.telegram_chat_id}")


COMANDOS = {
    "verificar": verificar_configuracao,
    "coletar": coletar,
    "avaliar": avaliar,
    "testar-telegram": testar_telegram,
    "rodar": rodar,
}


def configurar_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("google_genai").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def main() -> None:
    parser = argparse.ArgumentParser(prog="radar", description="Radar de Estágio")
    subcomandos = parser.add_subparsers(dest="comando")
    subcomandos.add_parser("rodar", help="executa o fluxo completo e envia a mensagem (padrão)")
    subcomandos.add_parser(
        "verificar", help="confere se as variáveis de ambiente estão preenchidas"
    )
    subcomandos.add_parser("coletar", help="busca vagas reais na Adzuna e imprime título e URL")
    subcomandos.add_parser(
        "avaliar", help="coleta, pré-filtra e avalia algumas vagas com o avaliador configurado"
    )
    subcomandos.add_parser("testar-telegram", help='envia "Radar OK" para o chat configurado')
    argumentos = parser.parse_args()

    configurar_logging()
    settings = carregar_settings()
    if settings is None:
        sys.exit(1)

    comando = COMANDOS[argumentos.comando or COMANDO_PADRAO]
    try:
        comando(settings)
    except (ErroDeColeta, ErroDeAvaliacao, ErroDeNotificacao) as erro:
        print(erro, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
