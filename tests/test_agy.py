import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from radar.domain.models import Vaga
from radar.matching.agy import ExtratorAgy
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


def test_extrai_vagas_com_saida_estruturada_do_agy():
    envelope = {
        "status": "SUCCESS",
        "structured_output": {
            "extracoes": [
                {
                    "id_vaga": "vaga-1",
                    "area_de_tecnologia": "compativel",
                    "cursos_aceitos": ["Engenharia de Software"],
                    "habilidades_obrigatorias": [],
                    "habilidades_desejaveis": ["Python", "SQL"],
                    "alerta_pegadinha": None,
                }
            ]
        },
    }
    extrator = ExtratorAgy(
        settings_de_teste(),
        executor=ExecutorFalso(ProcessoFalso(0, json.dumps(envelope))),
    )

    extracoes = extrator.extrair([vaga_exemplo()])

    assert len(extracoes) == 1
    assert extracoes[0].id_vaga == "vaga-1"
    assert extracoes[0].cursos_aceitos == ["Engenharia de Software"]
    assert extracoes[0].habilidades_desejaveis == ["Python", "SQL"]


def test_falha_do_processo_agy_vira_erro_de_avaliacao():
    extrator = ExtratorAgy(
        settings_de_teste(),
        executor=ExecutorFalso(ProcessoFalso(1, "", "sessão não autenticada")),
    )

    with pytest.raises(ErroDeAvaliacao, match="sessão não autenticada"):
        extrator.extrair([vaga_exemplo()])


def test_status_de_erro_do_agy_vira_erro_de_avaliacao():
    envelope = {"status": "ERROR", "error": "cota do Antigravity esgotada"}
    extrator = ExtratorAgy(
        settings_de_teste(),
        executor=ExecutorFalso(ProcessoFalso(0, json.dumps(envelope))),
    )

    with pytest.raises(ErroDeAvaliacao, match="cota do Antigravity esgotada"):
        extrator.extrair([vaga_exemplo()])


def test_timeout_do_agy_vira_erro_de_avaliacao():
    def executor_com_timeout(comando: list[str], **opcoes: object) -> ProcessoFalso:
        raise subprocess.TimeoutExpired(comando, timeout=300)

    extrator = ExtratorAgy(settings_de_teste(), executor=executor_com_timeout)

    with pytest.raises(ErroDeAvaliacao, match="tempo limite"):
        extrator.extrair([vaga_exemplo()])


def test_saida_invalida_do_agy_vira_erro_de_avaliacao():
    extrator = ExtratorAgy(
        settings_de_teste(),
        executor=ExecutorFalso(ProcessoFalso(0, "isto não é JSON")),
    )

    with pytest.raises(ErroDeAvaliacao, match="saída inválida"):
        extrator.extrair([vaga_exemplo()])


def test_saida_estruturada_fora_do_contrato_vira_erro_de_avaliacao():
    envelope = {"status": "SUCCESS", "structured_output": {"resultado": []}}
    extrator = ExtratorAgy(
        settings_de_teste(),
        executor=ExecutorFalso(ProcessoFalso(0, json.dumps(envelope))),
    )

    with pytest.raises(ErroDeAvaliacao, match="saída estruturada inválida"):
        extrator.extrair([vaga_exemplo()])


def test_agy_nao_instalado_vira_erro_de_avaliacao():
    def executor_sem_agy(comando: list[str], **opcoes: object) -> ProcessoFalso:
        raise FileNotFoundError("agy não encontrado")

    extrator = ExtratorAgy(settings_de_teste(), executor=executor_sem_agy)

    with pytest.raises(ErroDeAvaliacao, match="não foi possível executar o AGY"):
        extrator.extrair([vaga_exemplo()])


def test_sucesso_sem_saida_estruturada_vira_erro_de_avaliacao():
    envelope = {"status": "SUCCESS"}
    extrator = ExtratorAgy(
        settings_de_teste(),
        executor=ExecutorFalso(ProcessoFalso(0, json.dumps(envelope))),
    )

    with pytest.raises(ErroDeAvaliacao, match="saída estruturada ausente"):
        extrator.extrair([vaga_exemplo()])


def test_nao_entrega_segredos_do_radar_ao_processo_agy(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "segredo")
    executor = ExecutorFalso(
        ProcessoFalso(
            0,
            json.dumps({"status": "SUCCESS", "structured_output": {"extracoes": []}}),
        )
    )
    extrator = ExtratorAgy(settings_de_teste(), executor=executor)

    extrator.extrair([vaga_exemplo()])

    ambiente = executor.opcoes["env"]
    assert isinstance(ambiente, dict)
    assert "TELEGRAM_BOT_TOKEN" not in ambiente
