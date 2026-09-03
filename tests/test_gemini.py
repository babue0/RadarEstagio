import json
from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
from google.genai import errors

from radar.domain.models import Vaga
from radar.matching.errors import CotaDeAvaliacaoExcedida, ErroDeAvaliacao
from radar.matching.extracao import ExtracoesDeVagas
from radar.matching.gemini import ExtratorGemini
from radar.matching.prompt import montar_prompt
from radar.settings import Settings

MODELO_DE_TESTE = "modelo-de-teste"


def settings_de_teste() -> Settings:
    return Settings(
        _env_file=None,
        adzuna_app_id="app-id-de-teste",
        adzuna_app_key="app-key-de-teste",
        gemini_api_key="gemini-de-teste",
        gemini_modelo=MODELO_DE_TESTE,
        telegram_bot_token="token-de-teste",
        telegram_chat_id="123",
    )


def vaga_exemplo(numero: int = 1) -> Vaga:
    return Vaga(
        id_externo=str(numero),
        fonte="adzuna",
        titulo=f"Estágio em Desenvolvimento Python {numero}",
        empresa="Empresa Exemplo",
        localizacao="Rio de Janeiro, Rio de Janeiro",
        descricao="Buscamos estudante com Python e SQL. Trabalho remoto.",
        url=f"https://exemplo.com/vaga/{numero}",
        publicada_em=datetime(2026, 8, 25, tzinfo=UTC),
    )


@dataclass
class RespostaFalsa:
    text: str | None


class ModelsFalso:
    def __init__(self, resposta: RespostaFalsa | Exception) -> None:
        self._resposta = resposta
        self.chamadas: list[dict] = []

    def generate_content(self, **argumentos) -> RespostaFalsa:
        self.chamadas.append(argumentos)
        if isinstance(self._resposta, Exception):
            raise self._resposta
        return self._resposta


class ClienteFalso:
    def __init__(self, resposta: RespostaFalsa | Exception) -> None:
        self.models = ModelsFalso(resposta)


def extrator_com(resposta: RespostaFalsa | Exception) -> tuple[ExtratorGemini, ClienteFalso]:
    cliente = ClienteFalso(resposta)
    return ExtratorGemini(settings_de_teste(), cliente), cliente


def erro_da_api(codigo: int, mensagem: str) -> errors.APIError:
    return errors.APIError(codigo, {"error": {"message": mensagem, "status": "ERRO"}})


def extracao(numero: str, **alteracoes) -> dict:
    dados = {
        "id_vaga": numero,
        "area_de_tecnologia": "compativel",
        "cursos_aceitos": ["Ciência da Computação"],
        "aceita_qualquer_curso": False,
        "periodo_minimo": None,
        "experiencia_minima_anos": None,
        "habilidades_obrigatorias": [],
        "habilidades_desejaveis": ["Python", "SQL"],
        "alerta_pegadinha": None,
    }
    dados.update(alteracoes)
    return dados


def resposta_com(*extracoes: dict) -> RespostaFalsa:
    return RespostaFalsa(json.dumps({"extracoes": extracoes}))


def test_converte_json_do_gemini_em_extracoes_na_ordem_da_resposta():
    extrator, _ = extrator_com(
        resposta_com(
            extracao(
                "2",
                area_de_tecnologia="incompativel",
                cursos_aceitos=["Engenharia Elétrica"],
                periodo_minimo=6,
                habilidades_obrigatorias=["Java"],
                habilidades_desejaveis=[],
                alerta_pegadinha="Exige pleno.",
            ),
            extracao("1"),
        )
    )

    extracoes = extrator.extrair([vaga_exemplo(1), vaga_exemplo(2)])

    assert [item.id_vaga for item in extracoes] == ["2", "1"]
    assert extracoes[0].area_de_tecnologia == "incompativel"
    assert extracoes[0].cursos_aceitos == ["Engenharia Elétrica"]
    assert extracoes[0].periodo_minimo == 6
    assert extracoes[0].habilidades_obrigatorias == ["Java"]
    assert extracoes[0].alerta_pegadinha == "Exige pleno."
    assert extracoes[1].habilidades_desejaveis == ["Python", "SQL"]
    assert extracoes[1].alerta_pegadinha is None


def test_envia_prompt_de_lote_modelo_e_schema_json_ao_gemini():
    extrator, cliente = extrator_com(RespostaFalsa('{"extracoes": []}'))
    vagas = [vaga_exemplo(1), vaga_exemplo(2)]

    extrator.extrair(vagas)

    chamada = cliente.models.chamadas[0]
    assert chamada["model"] == MODELO_DE_TESTE
    assert chamada["contents"] == montar_prompt(vagas)
    assert chamada["config"].response_mime_type == "application/json"
    assert chamada["config"].response_schema is ExtracoesDeVagas
    assert chamada["config"].temperature == 0


def test_lista_vazia_nao_chama_o_modelo():
    extrator, cliente = extrator_com(RespostaFalsa(None))

    assert extrator.extrair([]) == []
    assert cliente.models.chamadas == []


def test_extracao_de_vaga_desconhecida_e_devolvida_para_o_pipeline_descartar():
    extrator, _ = extrator_com(resposta_com(extracao("1"), extracao("999")))

    extracoes = extrator.extrair([vaga_exemplo(1)])

    assert [item.id_vaga for item in extracoes] == ["1", "999"]


@pytest.mark.parametrize(
    "texto",
    [
        "isso não é json",
        '{"extracoes": [{"id_vaga": "1", "area_de_tecnologia": "talvez"}]}',
        '{"extracoes": [{"id_vaga": "1"}]}',
        '{"area_de_tecnologia": "compativel", "cursos_aceitos": ["formato antigo"]}',
        "",
        None,
    ],
)
def test_resposta_invalida_levanta_erro_de_avaliacao(texto: str | None):
    extrator, _ = extrator_com(RespostaFalsa(texto))

    with pytest.raises(ErroDeAvaliacao):
        extrator.extrair([vaga_exemplo()])


def test_erro_da_api_levanta_erro_de_avaliacao_com_status():
    extrator, _ = extrator_com(erro_da_api(503, "sobrecarga"))

    with pytest.raises(ErroDeAvaliacao, match="503") as capturado:
        extrator.extrair([vaga_exemplo()])
    assert not isinstance(capturado.value, CotaDeAvaliacaoExcedida)


def test_cota_excedida_levanta_erro_especifico():
    extrator, _ = extrator_com(erro_da_api(429, "quota"))

    with pytest.raises(CotaDeAvaliacaoExcedida) as capturado:
        extrator.extrair([vaga_exemplo()])
    assert capturado.value.aguardar_segundos is None


def test_cota_excedida_le_o_tempo_de_espera_da_mensagem():
    mensagem = "You exceeded your current quota.\nPlease retry in 15.319626475s."
    extrator, _ = extrator_com(erro_da_api(429, mensagem))

    with pytest.raises(CotaDeAvaliacaoExcedida) as capturado:
        extrator.extrair([vaga_exemplo()])
    assert capturado.value.aguardar_segundos == pytest.approx(15.32, abs=0.01)


def test_prompt_identifica_todas_as_vagas_sem_citar_candidato():
    prompt = montar_prompt([vaga_exemplo(1), vaga_exemplo(2)])

    assert "Vagas (2)" in prompt
    assert "Vaga id=1" in prompt
    assert "Vaga id=2" in prompt
    assert "Estágio em Desenvolvimento Python 2" in prompt
    assert "cursos_aceitos" in prompt
    assert "periodo_minimo" in prompt
    assert "alerta_pegadinha" in prompt
    assert "habilidades_obrigatorias" in prompt
    assert "habilidades_desejaveis" in prompt
