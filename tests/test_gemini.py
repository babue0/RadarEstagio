from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
from google.genai import errors

from radar.domain.models import Modalidade, Perfil, Vaga
from radar.matching.gemini import AvaliadorGemini, CotaDeAvaliacaoExcedida, ErroDeAvaliacao
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


def vaga_exemplo() -> Vaga:
    return Vaga(
        id_externo="1",
        fonte="adzuna",
        titulo="Estágio em Desenvolvimento Python",
        empresa="Empresa Exemplo",
        localizacao="Rio de Janeiro, Rio de Janeiro",
        descricao="Buscamos estudante com Python e SQL. Trabalho remoto.",
        url="https://exemplo.com/vaga/1",
        publicada_em=datetime(2026, 8, 25, tzinfo=UTC),
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


def avaliador_com(resposta: RespostaFalsa | Exception) -> tuple[AvaliadorGemini, ClienteFalso]:
    cliente = ClienteFalso(resposta)
    return AvaliadorGemini(settings_de_teste(), cliente), cliente


def test_converte_json_do_gemini_em_resultado_match():
    avaliador, _ = avaliador_com(
        RespostaFalsa(
            '{"nota": 85, "motivo": "Cumpre 2 de 2 requisitos.", "alerta_pegadinha": null}'
        )
    )

    resultado = avaliador.avaliar(vaga_exemplo(), perfil_exemplo())

    assert resultado.vaga == vaga_exemplo()
    assert resultado.nota == 85
    assert resultado.motivo == "Cumpre 2 de 2 requisitos."
    assert resultado.alerta_pegadinha is None


def test_preserva_alerta_de_pegadinha_quando_presente():
    avaliador, _ = avaliador_com(
        RespostaFalsa('{"nota": 20, "motivo": "Fora da área.", "alerta_pegadinha": "Exige pleno."}')
    )

    resultado = avaliador.avaliar(vaga_exemplo(), perfil_exemplo())

    assert resultado.alerta_pegadinha == "Exige pleno."


def test_envia_prompt_modelo_e_schema_json_ao_gemini():
    avaliador, cliente = avaliador_com(RespostaFalsa('{"nota": 50, "motivo": "ok"}'))

    avaliador.avaliar(vaga_exemplo(), perfil_exemplo())

    chamada = cliente.models.chamadas[0]
    assert chamada["model"] == MODELO_DE_TESTE
    assert chamada["contents"] == montar_prompt(vaga_exemplo(), perfil_exemplo())
    assert chamada["config"].response_mime_type == "application/json"
    assert chamada["config"].response_schema is not None


@pytest.mark.parametrize(
    "texto",
    [
        "isso não é json",
        '{"nota": 150, "motivo": "acima do limite"}',
        '{"motivo": "sem nota"}',
        "",
        None,
    ],
)
def test_resposta_invalida_levanta_erro_de_avaliacao(texto: str | None):
    avaliador, _ = avaliador_com(RespostaFalsa(texto))

    with pytest.raises(ErroDeAvaliacao):
        avaliador.avaliar(vaga_exemplo(), perfil_exemplo())


def test_erro_da_api_levanta_erro_de_avaliacao_com_status():
    avaliador, _ = avaliador_com(
        errors.APIError(
            429, {"error": {"message": "quota excedida", "status": "RESOURCE_EXHAUSTED"}}
        )
    )

    with pytest.raises(ErroDeAvaliacao, match="429"):
        avaliador.avaliar(vaga_exemplo(), perfil_exemplo())


def test_cota_excedida_levanta_erro_especifico():
    avaliador, _ = avaliador_com(
        errors.APIError(429, {"error": {"message": "quota", "status": "RESOURCE_EXHAUSTED"}})
    )

    with pytest.raises(CotaDeAvaliacaoExcedida):
        avaliador.avaliar(vaga_exemplo(), perfil_exemplo())


def test_outros_erros_da_api_nao_sao_cota_excedida():
    avaliador, _ = avaliador_com(
        errors.APIError(503, {"error": {"message": "sobrecarga", "status": "UNAVAILABLE"}})
    )

    with pytest.raises(ErroDeAvaliacao) as capturado:
        avaliador.avaliar(vaga_exemplo(), perfil_exemplo())
    assert not isinstance(capturado.value, CotaDeAvaliacaoExcedida)


def test_prompt_contem_perfil_e_vaga():
    prompt = montar_prompt(vaga_exemplo(), perfil_exemplo())

    assert "Engenharia de Software" in prompt
    assert "Python, SQL" in prompt
    assert "remoto" in prompt
    assert "Estágio em Desenvolvimento Python" in prompt
    assert "Empresa Exemplo" in prompt
    assert "alerta_pegadinha" in prompt
