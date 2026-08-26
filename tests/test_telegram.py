import json

import httpx
import pytest
from pytest_httpx import HTTPXMock

from radar.notification.formatador import LIMITE_DE_CARACTERES_DO_TELEGRAM
from radar.notification.telegram import ErroDeNotificacao, NotificadorTelegram
from radar.settings import Settings

TOKEN_DE_TESTE = "token-de-teste"
CHAT_ID_DE_TESTE = "123"


def settings_de_teste() -> Settings:
    return Settings(
        _env_file=None,
        adzuna_app_id="app-id-de-teste",
        adzuna_app_key="app-key-de-teste",
        gemini_api_key="gemini-de-teste",
        telegram_bot_token=TOKEN_DE_TESTE,
        telegram_chat_id=CHAT_ID_DE_TESTE,
    )


@pytest.fixture
def notificador():
    with httpx.Client() as cliente_http:
        yield NotificadorTelegram(settings_de_teste(), cliente_http)


def test_envia_mensagem_para_o_chat_com_html(
    httpx_mock: HTTPXMock, notificador: NotificadorTelegram
):
    httpx_mock.add_response(json={"ok": True})

    notificador.enviar("<b>Radar OK</b>")

    requisicao = httpx_mock.get_request()
    assert requisicao.method == "POST"
    assert str(requisicao.url) == f"https://api.telegram.org/bot{TOKEN_DE_TESTE}/sendMessage"
    corpo = json.loads(requisicao.content)
    assert corpo == {
        "chat_id": CHAT_ID_DE_TESTE,
        "text": "<b>Radar OK</b>",
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }


def test_texto_acima_do_limite_vira_varias_requisicoes(
    httpx_mock: HTTPXMock, notificador: NotificadorTelegram
):
    httpx_mock.add_response(json={"ok": True}, is_reusable=True)
    texto = "\n\n".join("bloco " + "x" * 1000 for _ in range(6))

    notificador.enviar(texto)

    requisicoes = httpx_mock.get_requests()
    assert len(requisicoes) > 1
    textos = [json.loads(requisicao.content)["text"] for requisicao in requisicoes]
    assert all(len(parte) <= LIMITE_DE_CARACTERES_DO_TELEGRAM for parte in textos)
    assert "\n\n".join(textos) == texto


def test_erro_http_levanta_erro_de_notificacao_com_descricao(
    httpx_mock: HTTPXMock, notificador: NotificadorTelegram
):
    httpx_mock.add_response(
        status_code=400, json={"ok": False, "description": "Bad Request: chat not found"}
    )

    with pytest.raises(ErroDeNotificacao, match="400.*chat not found"):
        notificador.enviar("Radar OK")


def test_falha_de_rede_levanta_erro_de_notificacao(
    httpx_mock: HTTPXMock, notificador: NotificadorTelegram
):
    httpx_mock.add_exception(httpx.ConnectError("sem conexão"))

    with pytest.raises(ErroDeNotificacao, match="ConnectError"):
        notificador.enviar("Radar OK")
