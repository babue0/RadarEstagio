import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from radar.domain.models import Modalidade, Perfil, Vaga
from radar.matching.agy import AvaliadorAgy
from radar.matching.errors import ErroDeAvaliacao
from radar.settings import Settings


def settings_de_teste() -> Settings:
    return Settings(
        _env_file=None,
        adzuna_app_id="app-id-de-teste",
        adzuna_app_key="app-key-de-teste",
        avaliador="agy",
        gemini_api_key="",
        agy_modelo="gemini-3.6-flash-low",
        telegram_bot_token="token-de-teste",
        telegram_chat_id="123",
    )


def vaga_exemplo() -> Vaga:
    return Vaga(
        id_externo="vaga-1",
        fonte="adzuna",
        titulo="Estágio em Python",
        empresa="Empresa Exemplo",
        localizacao="Rio de Janeiro, RJ",
        descricao="Python e SQL, trabalho remoto.",
        url="https://exemplo.com/vaga-1",
        publicada_em=datetime(2026, 8, 26, tzinfo=UTC),
    )


def perfil_exemplo() -> Perfil:
    return Perfil(
        curso="Engenharia de Software",
        periodo=4,
        habilidades=["Python", "SQL"],
        cidade="Rio de Janeiro, RJ",
        modalidade=Modalidade.REMOTO,
    )


@dataclass
class ProcessoFalso:
    returncode: int
    stdout: str
    stderr: str = ""


class ExecutorFalso:
    def __init__(self, resultado: ProcessoFalso) -> None:
        self.resultado = resultado
        self.opcoes: dict[str, object] = {}

    def __call__(self, comando: list[str], **opcoes: object) -> ProcessoFalso:
        self.opcoes = opcoes
        return self.resultado


def test_avalia_vagas_com_saida_estruturada_do_agy():
    envelope = {
        "status": "SUCCESS",
        "structured_output": {
            "avaliacoes": [
                {
                    "id_vaga": "vaga-1",
                    "nota": 88,
                    "motivo": "Compatível com Python e SQL.",
                    "alerta_pegadinha": None,
                }
            ]
        },
    }
    avaliador = AvaliadorAgy(
        settings_de_teste(),
        executor=ExecutorFalso(ProcessoFalso(0, json.dumps(envelope))),
    )

    resultados = avaliador.avaliar([vaga_exemplo()], perfil_exemplo())

    assert len(resultados) == 1
    assert resultados[0].vaga.id_externo == "vaga-1"
    assert resultados[0].nota == 88
    assert resultados[0].motivo == "Compatível com Python e SQL."


def test_falha_do_processo_agy_vira_erro_de_avaliacao():
    avaliador = AvaliadorAgy(
        settings_de_teste(),
        executor=ExecutorFalso(ProcessoFalso(1, "", "sessão não autenticada")),
    )

    with pytest.raises(ErroDeAvaliacao, match="sessão não autenticada"):
        avaliador.avaliar([vaga_exemplo()], perfil_exemplo())


def test_status_de_erro_do_agy_vira_erro_de_avaliacao():
    envelope = {"status": "ERROR", "error": "cota do Antigravity esgotada"}
    avaliador = AvaliadorAgy(
        settings_de_teste(),
        executor=ExecutorFalso(ProcessoFalso(0, json.dumps(envelope))),
    )

    with pytest.raises(ErroDeAvaliacao, match="cota do Antigravity esgotada"):
        avaliador.avaliar([vaga_exemplo()], perfil_exemplo())


def test_timeout_do_agy_vira_erro_de_avaliacao():
    def executor_com_timeout(comando: list[str], **opcoes: object) -> ProcessoFalso:
        raise subprocess.TimeoutExpired(comando, timeout=300)

    avaliador = AvaliadorAgy(settings_de_teste(), executor=executor_com_timeout)

    with pytest.raises(ErroDeAvaliacao, match="tempo limite"):
        avaliador.avaliar([vaga_exemplo()], perfil_exemplo())


def test_saida_invalida_do_agy_vira_erro_de_avaliacao():
    avaliador = AvaliadorAgy(
        settings_de_teste(),
        executor=ExecutorFalso(ProcessoFalso(0, "isto não é JSON")),
    )

    with pytest.raises(ErroDeAvaliacao, match="saída inválida"):
        avaliador.avaliar([vaga_exemplo()], perfil_exemplo())


def test_saida_estruturada_fora_do_contrato_vira_erro_de_avaliacao():
    envelope = {"status": "SUCCESS", "structured_output": {"resultado": []}}
    avaliador = AvaliadorAgy(
        settings_de_teste(),
        executor=ExecutorFalso(ProcessoFalso(0, json.dumps(envelope))),
    )

    with pytest.raises(ErroDeAvaliacao, match="saída estruturada inválida"):
        avaliador.avaliar([vaga_exemplo()], perfil_exemplo())


def test_agy_nao_instalado_vira_erro_de_avaliacao():
    def executor_sem_agy(comando: list[str], **opcoes: object) -> ProcessoFalso:
        raise FileNotFoundError("agy não encontrado")

    avaliador = AvaliadorAgy(settings_de_teste(), executor=executor_sem_agy)

    with pytest.raises(ErroDeAvaliacao, match="não foi possível executar o AGY"):
        avaliador.avaliar([vaga_exemplo()], perfil_exemplo())


def test_sucesso_sem_saida_estruturada_vira_erro_de_avaliacao():
    envelope = {"status": "SUCCESS"}
    avaliador = AvaliadorAgy(
        settings_de_teste(),
        executor=ExecutorFalso(ProcessoFalso(0, json.dumps(envelope))),
    )

    with pytest.raises(ErroDeAvaliacao, match="saída estruturada ausente"):
        avaliador.avaliar([vaga_exemplo()], perfil_exemplo())


def test_nao_entrega_segredos_do_radar_ao_processo_agy(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "segredo")
    executor = ExecutorFalso(
        ProcessoFalso(
            0,
            json.dumps({"status": "SUCCESS", "structured_output": {"avaliacoes": []}}),
        )
    )
    avaliador = AvaliadorAgy(settings_de_teste(), executor=executor)

    avaliador.avaliar([vaga_exemplo()], perfil_exemplo())

    ambiente = executor.opcoes["env"]
    assert isinstance(ambiente, dict)
    assert "TELEGRAM_BOT_TOKEN" not in ambiente
