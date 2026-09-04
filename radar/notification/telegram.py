import httpx

from radar.domain.models import BotaoDeFeedback, PerguntaDeFeedback
from radar.notification.formatador import dividir_em_mensagens

URL_BASE_DA_API = "https://api.telegram.org"


class ErroDeNotificacao(Exception):
    pass


class NotificadorTelegram:
    def __init__(self, token_do_bot: str, cliente_http: httpx.Client) -> None:
        self._url_envio = f"{URL_BASE_DA_API}/bot{token_do_bot}/sendMessage"
        self._cliente_http = cliente_http

    def enviar(self, chat_id: str, texto: str) -> None:
        for mensagem in dividir_em_mensagens(texto):
            self._enviar_mensagem(chat_id, mensagem)

    def enviar_pergunta(self, chat_id: str, pergunta: PerguntaDeFeedback) -> None:
        self._postar(
            {
                "chat_id": chat_id,
                "text": pergunta.texto,
                "disable_notification": True,
                "reply_markup": {"inline_keyboard": teclado(pergunta.linhas_de_botoes)},
            }
        )

    def _enviar_mensagem(self, chat_id: str, mensagem: str) -> None:
        self._postar(
            {
                "chat_id": chat_id,
                "text": mensagem,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
        )

    def _postar(self, corpo: dict) -> None:
        try:
            resposta = self._cliente_http.post(self._url_envio, json=corpo)
            resposta.raise_for_status()
        except httpx.HTTPStatusError as erro:
            status = erro.response.status_code
            descricao = erro.response.json().get("description", "")
            raise ErroDeNotificacao(f"Telegram respondeu HTTP {status}: {descricao}") from None
        except httpx.HTTPError as erro:
            raise ErroDeNotificacao(
                f"Falha de rede ao enviar mensagem no Telegram ({type(erro).__name__})"
            ) from erro


def teclado(linhas: list[list[BotaoDeFeedback]]) -> list[list[dict]]:
    return [
        [{"text": botao.rotulo, "callback_data": botao.dados} for botao in linha]
        for linha in linhas
    ]
