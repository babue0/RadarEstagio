import httpx

from radar.domain.models import BotaoDeFeedback, MensagemDaRecomendacao
from radar.notification.formatador import dividir_em_mensagens

URL_BASE_DA_API = "https://api.telegram.org"
BOTOES_POR_LINHA = 2


class ErroDeNotificacao(Exception):
    pass


class NotificadorTelegram:
    def __init__(self, token_do_bot: str, cliente_http: httpx.Client) -> None:
        self._url_envio = f"{URL_BASE_DA_API}/bot{token_do_bot}/sendMessage"
        self._cliente_http = cliente_http

    def enviar(self, chat_id: str, texto: str) -> None:
        for mensagem in dividir_em_mensagens(texto):
            self._postar(corpo_da_mensagem(chat_id, mensagem))

    def enviar_recomendacoes(self, chat_id: str, mensagens: list[MensagemDaRecomendacao]) -> None:
        for posicao, mensagem in enumerate(mensagens):
            corpo = corpo_da_mensagem(chat_id, mensagem.texto)
            corpo["reply_markup"] = {"inline_keyboard": teclado(mensagem.botoes)}
            if posicao > 0:
                corpo["disable_notification"] = True
            self._postar(corpo)

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


def corpo_da_mensagem(chat_id: str, texto: str) -> dict:
    return {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }


def teclado(botoes: list[BotaoDeFeedback]) -> list[list[dict]]:
    linhas = []
    for inicio in range(0, len(botoes), BOTOES_POR_LINHA):
        linhas.append(
            [
                {"text": botao.rotulo, "callback_data": dado_do_botao(botao)}
                for botao in botoes[inicio : inicio + BOTOES_POR_LINHA]
            ]
        )
    return linhas


def dado_do_botao(botao: BotaoDeFeedback) -> str:
    return f"{botao.acao.value}:{botao.token}"
