from datetime import UTC, datetime

from radar.domain.models import Modalidade, Perfil, Vaga
from radar.matching.avaliacoes import AvaliacaoIA, AvaliacoesIA, casar_avaliacoes_com_vagas


def vaga(modalidade: Modalidade | None = None) -> Vaga:
    return Vaga(
        id_externo="vaga-1",
        fonte="adzuna",
        titulo="Estágio em Desenvolvimento Web",
        empresa="Empresa Exemplo",
        localizacao="Rio de Janeiro, RJ",
        descricao="Descrição",
        url="https://exemplo.com/vaga-1",
        publicada_em=datetime(2026, 8, 30, tzinfo=UTC),
        modalidade=modalidade,
    )


def perfil(habilidades: list[str] | None = None) -> Perfil:
    return Perfil(
        curso="Engenharia de Software",
        periodo=4,
        habilidades=["Python", "Java"] if habilidades is None else habilidades,
        cidade="Rio de Janeiro, RJ",
        modalidade=Modalidade.PRESENCIAL,
    )


def avaliacao(**alteracoes) -> AvaliacaoIA:
    dados = {
        "id_vaga": "vaga-1",
        "area": "compativel",
        "curso": "compativel",
        "periodo_experiencia": "compativel",
        "habilidades_obrigatorias": [],
        "habilidades_desejaveis": [],
    }
    dados.update(alteracoes)
    return AvaliacaoIA.model_validate(dados)


def resultado_da(avaliacao_ia: AvaliacaoIA, candidato: Perfil | None = None):
    resultados = casar_avaliacoes_com_vagas(
        AvaliacoesIA(avaliacoes=[avaliacao_ia]), [vaga()], candidato or perfil()
    )
    return resultados[0]


def test_stack_desejavel_sem_correspondencia_recebe_48_pontos():
    requisitos = ["PHP", "MySQL", "SQL", "HTML5", "JavaScript", "REST", "VueJS", "AJAX", "jQuery"]

    resultado = resultado_da(avaliacao(habilidades_desejaveis=requisitos))

    assert resultado.nota == 48


def test_java_nao_corresponde_a_javascript():
    resultado = resultado_da(avaliacao(habilidades_desejaveis=["JavaScript"]))

    assert resultado.nota == 48


def test_vaga_sem_stack_declarada_atende_o_fator_de_habilidades():
    resultado = resultado_da(avaliacao())

    assert resultado.nota == 98


def test_alias_js_corresponde_a_javascript():
    resultado = resultado_da(
        avaliacao(habilidades_desejaveis=["JavaScript"]), perfil(habilidades=["JS"])
    )

    assert resultado.nota == 98


def test_cobertura_total_da_stack_desejavel_recebe_98_pontos():
    resultado = resultado_da(avaliacao(habilidades_desejaveis=["Python", "Java"]))

    assert resultado.nota == 98


def test_obrigatorias_valem_oitenta_porcento_quando_ha_desejaveis():
    resultado = resultado_da(
        avaliacao(
            habilidades_obrigatorias=["Python", "JavaScript"],
            habilidades_desejaveis=["SQL"],
        )
    )

    assert resultado.nota == 68


def test_fatores_parciais_recebem_metade_do_peso():
    resultado = resultado_da(
        avaliacao(
            area="parcial",
            curso="parcial",
            periodo_experiencia="parcial",
            habilidades_obrigatorias=["Python"],
        )
    )

    assert resultado.nota == 78
