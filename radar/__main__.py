import argparse
import logging
import sys
from datetime import UTC, datetime

import httpx
from pydantic import ValidationError

from radar.collectors.errors import ErroDeColeta
from radar.collectors.factory import cidades_de_interesse, criar_coletor
from radar.domain.models import Usuario
from radar.domain.perfil_fixo import perfil_do_mvp
from radar.domain.ports import ColetorDeVagas, Repositorio
from radar.filtering.duplicatas import remover_duplicatas
from radar.filtering.prefiltro import filtrar
from radar.matching.enriquecimento import AvaliadorComDescricoesCompletas
from radar.matching.errors import ErroDeAvaliacao
from radar.matching.factory import criar_avaliador, nome_do_modelo
from radar.matching.lotes import AvaliadorEmLotes
from radar.notification.telegram import ErroDeNotificacao, NotificadorTelegram
from radar.pipeline import ParametrosDaExecucao, executar
from radar.settings import Settings
from radar.storage.errors import ErroDeArmazenamento
from radar.storage.factory import abrir_repositorio, abrir_repositorio_em_memoria

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
    print(f"Fontes: {', '.join(settings.fontes_selecionadas())}")
    print(f"Dias recentes: {settings.dias_recentes}")
    print(f"Vagas enviadas por execução: {settings.quantidade_vagas_enviadas}")
    print(f"Nota mínima para entrar na mensagem: {settings.nota_minima}")
    if not settings.usa_banco():
        print("Banco: nenhum (perfil fixo)")
        return
    with abrir_repositorio(settings) as repositorio:
        usuarios = repositorio.listar_ativos()
    print(f"Banco: conectado, {len(usuarios)} usuários ativos com Telegram vinculado")


def coletar(settings: Settings) -> None:
    usuarios = listar_usuarios(settings)
    with httpx.Client(timeout=TIMEOUT_HTTP_EM_SEGUNDOS) as cliente_http:
        coletadas = montar_coletor(settings, cliente_http, usuarios).coletar()
    vagas = remover_duplicatas(coletadas)
    print(f"{len(coletadas)} vagas coletadas, {len(vagas)} após remover duplicatas")
    for vaga in vagas:
        modalidade = vaga.modalidade.value if vaga.modalidade else "modalidade não informada"
        print(
            f"- [{vaga.fonte}] {vaga.titulo} | {vaga.empresa} | {vaga.localizacao} | {modalidade}"
        )
        print(f"  {vaga.url}")


def avaliar(settings: Settings) -> None:
    perfil = perfil_do_mvp()
    usuarios = listar_usuarios(settings)
    with httpx.Client(timeout=TIMEOUT_HTTP_EM_SEGUNDOS) as cliente_http:
        coletadas = montar_coletor(settings, cliente_http, usuarios).coletar()
        vagas = filtrar(remover_duplicatas(coletadas), perfil)
        selecionadas = vagas[:LIMITE_DE_VAGAS_NA_AVALIACAO_MANUAL]
        print(
            f"{len(vagas)} vagas após o pré-filtro; "
            f"avaliando {len(selecionadas)} com {settings.avaliador}"
        )
        resultados = montar_avaliador(settings, cliente_http).avaliar(selecionadas, perfil)
    for resultado in resultados:
        vaga = resultado.vaga
        print(f"- [{resultado.nota:3d}] {vaga.titulo} | {vaga.empresa} | {vaga.localizacao}")
        print(f"  A favor: {', '.join(resultado.pontos_a_favor) or '-'}")
        print(f"  Contra: {', '.join(resultado.pontos_contra) or '-'}")
        if resultado.alerta_pegadinha:
            print(f"  Alerta: {resultado.alerta_pegadinha}")


def testar_telegram(settings: Settings) -> None:
    with httpx.Client(timeout=TIMEOUT_HTTP_EM_SEGUNDOS) as cliente_http:
        NotificadorTelegram(settings.telegram_bot_token, cliente_http).enviar(
            settings.telegram_chat_id, "Radar OK"
        )
    print(f"Mensagem enviada para o chat {settings.telegram_chat_id}")


def listar_usuarios(settings: Settings) -> list[Usuario]:
    with abrir_repositorio(settings) as repositorio:
        return repositorio.listar_ativos()


def montar_coletor(
    settings: Settings, cliente_http: httpx.Client, usuarios: list[Usuario]
) -> ColetorDeVagas:
    cidades = cidades_de_interesse(usuarios)
    return criar_coletor(settings, cliente_http, datetime.now(UTC), cidades)


def montar_avaliador(settings: Settings, cliente_http: httpx.Client) -> AvaliadorEmLotes:
    com_descricoes_completas = AvaliadorComDescricoesCompletas(
        criar_avaliador(settings), cliente_http
    )
    return AvaliadorEmLotes(com_descricoes_completas, settings.gemini_vagas_por_lote)


def executar_fluxo(
    settings: Settings, cliente_http: httpx.Client, repositorio: Repositorio
) -> None:
    coletor = montar_coletor(settings, cliente_http, repositorio.listar_ativos())
    enviadas = executar(
        coletor,
        montar_avaliador(settings, cliente_http),
        NotificadorTelegram(settings.telegram_bot_token, cliente_http),
        repositorio,
        ParametrosDaExecucao(
            modelo=nome_do_modelo(settings),
            quantidade=settings.quantidade_vagas_enviadas,
            nota_minima=settings.nota_minima,
            falhas_ate_pausar=settings.falhas_de_envio_ate_pausar,
            dias_de_silencio_ate_avisar=settings.dias_de_silencio_ate_avisar,
        ),
        datetime.now(UTC),
    )
    total = sum(len(selecionadas) for selecionadas in enviadas.values())
    print(f"{total} vagas enviadas para {len(enviadas)} usuários")


def rodar(settings: Settings) -> None:
    with (
        httpx.Client(timeout=TIMEOUT_HTTP_EM_SEGUNDOS) as cliente_http,
        abrir_repositorio(settings) as repositorio,
    ):
        executar_fluxo(settings, cliente_http, repositorio)


def testar_local(settings: Settings) -> None:
    print("Modo local: banco e histórico ignorados; todas as vagas serão avaliadas novamente.")
    with (
        httpx.Client(timeout=TIMEOUT_HTTP_EM_SEGUNDOS) as cliente_http,
        abrir_repositorio_em_memoria(settings) as repositorio,
    ):
        executar_fluxo(settings, cliente_http, repositorio)


COMANDOS = {
    "verificar": verificar_configuracao,
    "coletar": coletar,
    "avaliar": avaliar,
    "testar-telegram": testar_telegram,
    "testar-local": testar_local,
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
    subcomandos.add_parser(
        "coletar", help="busca vagas reais nas fontes configuradas e imprime título e URL"
    )
    subcomandos.add_parser(
        "avaliar", help="coleta, pré-filtra e avalia algumas vagas com o avaliador configurado"
    )
    subcomandos.add_parser("testar-telegram", help='envia "Radar OK" para o chat configurado')
    subcomandos.add_parser(
        "testar-local",
        help="executa o fluxo completo sem banco ou histórico e envia ao Telegram",
    )
    argumentos = parser.parse_args()

    configurar_logging()
    settings = carregar_settings()
    if settings is None:
        sys.exit(1)

    comando = COMANDOS[argumentos.comando or COMANDO_PADRAO]
    try:
        comando(settings)
    except (ErroDeColeta, ErroDeAvaliacao, ErroDeNotificacao, ErroDeArmazenamento) as erro:
        print(erro, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
