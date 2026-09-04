import json
from uuid import UUID

import httpx
import pytest
from pytest_httpx import HTTPXMock

from radar.domain.models import AcaoDeFeedback, BotaoDeFeedback, MensagemDaRecomendacao
from radar.notification.formatador import LIMITE_DE_CARACTERES_DO_TELEGRAM
from radar.notification.telegram import ErroDeNotificacao, NotificadorTelegram

TOKEN_DE_TESTE = "token-de-teste"
CHAT_ID_DE_TESTE = "123"
TOKEN_DO_ENVIO = UUID("3f2504e0-4f89-11d3-9a0c-0305e82c3301")
LIMITE_DE_BYTES_DO_CALLBACK_DATA = 64


def recomendacao(texto: str) -> MensagemDaRecomendacao:
    return MensagemDaRecomendacao(
        texto=texto,
        botoes=[
            BotaoDeFeedback(
                rotulo="👍 Faz sentido", acao=AcaoDeFeedback.UTIL, token=TOKEN_DO_ENVIO
            ),
            BotaoDeFeedback(
                rotulo="👎 Não serve", acao=AcaoDeFeedback.IRRELEVANTE, token=TOKEN_DO_ENVIO
            ),
            BotaoDeFeedback(
                rotulo="Candidatei-me", acao=AcaoDeFeedback.CANDIDATURA, token=TOKEN_DO_ENVIO
            ),
        ],
    )


@pytest.fixture
def notificador():
    with httpx.Client() as cliente_http:
        yield NotificadorTelegram(TOKEN_DE_TESTE, cliente_http)


def test_envia_mensagem_para_o_chat_com_html(
    httpx_mock: HTTPXMock, notificador: NotificadorTelegram
):
    httpx_mock.add_response(json={"ok": True})

    notificador.enviar(CHAT_ID_DE_TESTE, "<b>Radar OK</b>")

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
    texto = "\n\n───────────────\n\n".join("bloco " + "x" * 1000 for _ in range(6))

    notificador.enviar(CHAT_ID_DE_TESTE, texto)

    requisicoes = httpx_mock.get_requests()
    assert len(requisicoes) > 1
    textos = [json.loads(requisicao.content)["text"] for requisicao in requisicoes]
    assert all(len(parte) <= LIMITE_DE_CARACTERES_DO_TELEGRAM for parte in textos)
    assert "\n\n───────────────\n\n".join(textos) == texto


def test_erro_http_levanta_erro_de_notificacao_com_descricao(
    httpx_mock: HTTPXMock, notificador: NotificadorTelegram
):
    httpx_mock.add_response(
        status_code=400, json={"ok": False, "description": "Bad Request: chat not found"}
    )

    with pytest.raises(ErroDeNotificacao, match="400.*chat not found"):
        notificador.enviar(CHAT_ID_DE_TESTE, "Radar OK")


def test_falha_de_rede_levanta_erro_de_notificacao(
    httpx_mock: HTTPXMock, notificador: NotificadorTelegram
):
    httpx_mock.add_exception(httpx.ConnectError("sem conexão"))

    with pytest.raises(ErroDeNotificacao, match="ConnectError"):
        notificador.enviar(CHAT_ID_DE_TESTE, "Radar OK")


def test_cada_recomendacao_vira_uma_mensagem_com_teclado_inline(
    httpx_mock: HTTPXMock, notificador: NotificadorTelegram
):
    httpx_mock.add_response(json={"ok": True}, is_reusable=True)

    notificador.enviar_recomendacoes(
        CHAT_ID_DE_TESTE, [recomendacao("Vaga 1"), recomendacao("Vaga 2")]
    )

    corpos = [json.loads(requisicao.content) for requisicao in httpx_mock.get_requests()]
    assert [corpo["text"] for corpo in corpos] == ["Vaga 1", "Vaga 2"]
    assert corpos[0]["reply_markup"] == {
        "inline_keyboard": [
            [
                {"text": "👍 Faz sentido", "callback_data": f"util:{TOKEN_DO_ENVIO}"},
                {"text": "👎 Não serve", "callback_data": f"irrelevante:{TOKEN_DO_ENVIO}"},
            ],
            [{"text": "Candidatei-me", "callback_data": f"candidatura:{TOKEN_DO_ENVIO}"}],
        ]
    }


def test_so_a_primeira_recomendacao_do_dia_notifica(
    httpx_mock: HTTPXMock, notificador: NotificadorTelegram
):
    httpx_mock.add_response(json={"ok": True}, is_reusable=True)

    notificador.enviar_recomendacoes(
        CHAT_ID_DE_TESTE,
        [recomendacao("Vaga 1"), recomendacao("Vaga 2"), recomendacao("Vaga 3")],
    )

    corpos = [json.loads(requisicao.content) for requisicao in httpx_mock.get_requests()]
    assert "disable_notification" not in corpos[0]
    assert [corpo["disable_notification"] for corpo in corpos[1:]] == [True, True]


def test_callback_data_cabe_no_limite_do_telegram(
    httpx_mock: HTTPXMock, notificador: NotificadorTelegram
):
    httpx_mock.add_response(json={"ok": True})

    notificador.enviar_recomendacoes(CHAT_ID_DE_TESTE, [recomendacao("Vaga 1")])

    corpo = json.loads(httpx_mock.get_request().content)
    dados = [
        botao["callback_data"]
        for linha in corpo["reply_markup"]["inline_keyboard"]
        for botao in linha
    ]
    assert all(len(dado.encode()) <= LIMITE_DE_BYTES_DO_CALLBACK_DATA for dado in dados)
