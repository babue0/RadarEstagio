import httpx

from radar.notification.formatador import dividir_em_mensagens
from radar.settings import Settings

URL_BASE_DA_API = "https://api.telegram.org"


class ErroDeNotificacao(Exception):
    pass


class NotificadorTelegram:
    def __init__(self, settings: Settings, cliente_http: httpx.Client) -> None:
        self._url_envio = f"{URL_BASE_DA_API}/bot{settings.telegram_bot_token}/sendMessage"
        self._chat_id = settings.telegram_chat_id
        self._cliente_http = cliente_http

    def enviar(self, texto: str) -> None:
        for mensagem in dividir_em_mensagens(texto):
            self._enviar_mensagem(mensagem)

    def _enviar_mensagem(self, mensagem: str) -> None:
        try:
            resposta = self._cliente_http.post(
                self._url_envio,
                json={
                    "chat_id": self._chat_id,
                    "text": mensagem,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
            )
            resposta.raise_for_status()
        except httpx.HTTPStatusError as erro:
            status = erro.response.status_code
            descricao = erro.response.json().get("description", "")
            raise ErroDeNotificacao(f"Telegram respondeu HTTP {status}: {descricao}") from None
        except httpx.HTTPError as erro:
            raise ErroDeNotificacao(
                f"Falha de rede ao enviar mensagem no Telegram ({type(erro).__name__})"
            ) from erro
