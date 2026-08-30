import json
import os
import subprocess
from collections.abc import Callable
from tempfile import TemporaryDirectory

from pydantic import ValidationError

from radar.domain.models import Perfil, ResultadoMatch, Vaga
from radar.matching.avaliacoes import AvaliacoesIA, casar_avaliacoes_com_vagas
from radar.matching.errors import ErroDeAvaliacao
from radar.matching.prompt import montar_prompt
from radar.settings import Settings

VARIAVEIS_SENSIVEIS_DO_RADAR = frozenset(
    {
        "ADZUNA_APP_ID",
        "ADZUNA_APP_KEY",
        "GEMINI_API_KEY",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
    }
)


class AvaliadorAgy:
    def __init__(
        self,
        settings: Settings,
        executor: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
        self._modelo = settings.agy_modelo
        self._timeout_segundos = settings.agy_timeout_segundos
        self._executor = executor

    def avaliar(self, vagas: list[Vaga], perfil: Perfil) -> list[ResultadoMatch]:
        if not vagas:
            return []

        schema = json.dumps(AvaliacoesIA.model_json_schema(), ensure_ascii=False)
        ambiente = os.environ.copy()
        for variavel in VARIAVEIS_SENSIVEIS_DO_RADAR:
            ambiente.pop(variavel, None)
        try:
            with TemporaryDirectory(prefix="radar-agy-") as diretorio:
                processo = self._executor(
                    [
                        "agy",
                        "--print",
                        montar_prompt(vagas, perfil),
                        "--model",
                        self._modelo,
                        "--output-format",
                        "json",
                        "--json-schema",
                        schema,
                        "--sandbox",
                        "--disable-slash-commands",
                        "--print-timeout",
                        f"{self._timeout_segundos}s",
                    ],
                    capture_output=True,
                    text=True,
                    cwd=diretorio,
                    check=False,
                    timeout=self._timeout_segundos,
                    env=ambiente,
                )
        except subprocess.TimeoutExpired:
            raise ErroDeAvaliacao(
                f"AGY excedeu o tempo limite de {self._timeout_segundos} segundos"
            ) from None
        except OSError as erro:
            raise ErroDeAvaliacao(f"não foi possível executar o AGY: {erro}") from None

        if processo.returncode != 0:
            detalhe = processo.stderr.strip() or "processo terminou sem detalhes"
            raise ErroDeAvaliacao(f"AGY falhou: {detalhe}")

        try:
            envelope = json.loads(processo.stdout)
        except json.JSONDecodeError as erro:
            raise ErroDeAvaliacao(f"AGY devolveu saída inválida: {erro}") from None
        if envelope.get("status") != "SUCCESS":
            detalhe = envelope.get("error") or f"status {envelope.get('status', 'desconhecido')}"
            raise ErroDeAvaliacao(f"AGY falhou: {detalhe}")
        if "structured_output" not in envelope:
            raise ErroDeAvaliacao("AGY devolveu saída estruturada ausente")
        try:
            avaliacoes = AvaliacoesIA.model_validate(envelope["structured_output"])
        except ValidationError as erro:
            raise ErroDeAvaliacao(f"AGY devolveu saída estruturada inválida: {erro}") from None
        return casar_avaliacoes_com_vagas(avaliacoes, vagas, perfil)
