from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
from google.genai import errors

from radar.domain.models import Modalidade, Perfil, Vaga
from radar.matching.errors import CotaDeAvaliacaoExcedida, ErroDeAvaliacao
from radar.matching.gemini import AvaliadorGemini
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


def erro_da_api(codigo: int, mensagem: str) -> errors.APIError:
    return errors.APIError(codigo, {"error": {"message": mensagem, "status": "ERRO"}})


def test_converte_json_do_gemini_em_resultados_na_ordem_da_resposta():
    avaliador, _ = avaliador_com(
        RespostaFalsa(
            '{"avaliacoes": ['
            '{"id_vaga": "2", "nota": 40, "motivo": "Fraco.", "alerta_pegadinha": "Exige pleno."},'
            '{"id_vaga": "1", "nota": 85, "motivo": "Cumpre 2 de 2.", "alerta_pegadinha": null}'
            "]}"
        )
    )

    resultados = avaliador.avaliar([vaga_exemplo(1), vaga_exemplo(2)], perfil_exemplo())

    assert [(r.vaga.id_externo, r.nota) for r in resultados] == [("2", 40), ("1", 85)]
    assert resultados[0].alerta_pegadinha == "Exige pleno."
    assert resultados[1].motivo == "Cumpre 2 de 2."
    assert resultados[1].alerta_pegadinha is None


def test_envia_prompt_de_lote_modelo_e_schema_json_ao_gemini():
    avaliador, cliente = avaliador_com(RespostaFalsa('{"avaliacoes": []}'))
    vagas = [vaga_exemplo(1), vaga_exemplo(2)]

    avaliador.avaliar(vagas, perfil_exemplo())

    chamada = cliente.models.chamadas[0]
    assert chamada["model"] == MODELO_DE_TESTE
    assert chamada["contents"] == montar_prompt(vagas, perfil_exemplo())
    assert chamada["config"].response_mime_type == "application/json"
    assert chamada["config"].response_schema is not None


def test_lista_vazia_nao_chama_o_gemini():
    avaliador, cliente = avaliador_com(RespostaFalsa('{"avaliacoes": []}'))

    assert avaliador.avaliar([], perfil_exemplo()) == []
    assert cliente.models.chamadas == []


def test_ignora_avaliacoes_com_id_desconhecido_ou_repetido():
    avaliador, _ = avaliador_com(
        RespostaFalsa(
            '{"avaliacoes": ['
            '{"id_vaga": "1", "nota": 80, "motivo": "primeira"},'
            '{"id_vaga": "1", "nota": 10, "motivo": "repetida"},'
            '{"id_vaga": "999", "nota": 50, "motivo": "inventada"}'
            "]}"
        )
    )

    resultados = avaliador.avaliar([vaga_exemplo(1)], perfil_exemplo())

    assert [(r.vaga.id_externo, r.motivo) for r in resultados] == [("1", "primeira")]


def test_vaga_ausente_na_resposta_simplesmente_nao_e_devolvida():
    avaliador, _ = avaliador_com(
        RespostaFalsa('{"avaliacoes": [{"id_vaga": "1", "nota": 80, "motivo": "ok"}]}')
    )

    resultados = avaliador.avaliar([vaga_exemplo(1), vaga_exemplo(2)], perfil_exemplo())

    assert [r.vaga.id_externo for r in resultados] == ["1"]


@pytest.mark.parametrize(
    "texto",
    [
        "isso não é json",
        '{"avaliacoes": [{"id_vaga": "1", "nota": 150, "motivo": "acima do limite"}]}',
        '{"avaliacoes": [{"id_vaga": "1", "motivo": "sem nota"}]}',
        '{"nota": 50, "motivo": "formato antigo, sem lista"}',
        "",
        None,
    ],
)
def test_resposta_invalida_levanta_erro_de_avaliacao(texto: str | None):
    avaliador, _ = avaliador_com(RespostaFalsa(texto))

    with pytest.raises(ErroDeAvaliacao):
        avaliador.avaliar([vaga_exemplo()], perfil_exemplo())


def test_erro_da_api_levanta_erro_de_avaliacao_com_status():
    avaliador, _ = avaliador_com(erro_da_api(503, "sobrecarga"))

    with pytest.raises(ErroDeAvaliacao, match="503") as capturado:
        avaliador.avaliar([vaga_exemplo()], perfil_exemplo())
    assert not isinstance(capturado.value, CotaDeAvaliacaoExcedida)


def test_cota_excedida_levanta_erro_especifico():
    avaliador, _ = avaliador_com(erro_da_api(429, "quota"))

    with pytest.raises(CotaDeAvaliacaoExcedida):
        avaliador.avaliar([vaga_exemplo()], perfil_exemplo())


def test_prompt_contem_perfil_e_todas_as_vagas_identificadas():
    prompt = montar_prompt([vaga_exemplo(1), vaga_exemplo(2)], perfil_exemplo())

    assert "Engenharia de Software" in prompt
    assert "Python, SQL" in prompt
    assert "remoto" in prompt
    assert "Vagas (2)" in prompt
    assert "Vaga id=1" in prompt
    assert "Vaga id=2" in prompt
    assert "Estágio em Desenvolvimento Python 2" in prompt
    assert "alerta_pegadinha" in prompt
