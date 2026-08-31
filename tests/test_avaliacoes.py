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


def test_stack_desejavel_sem_correspondencia_recebe_nota_baixa():
    requisitos = ["PHP", "MySQL", "SQL", "HTML5", "JavaScript", "REST", "VueJS", "AJAX", "jQuery"]

    resultado = resultado_da(avaliacao(habilidades_desejaveis=requisitos))

    assert resultado.nota == 53


def test_muitos_requisitos_ausentes_pesam_mais_que_um_so():
    muitos = ["PHP", "MySQL", "HTML5", "VueJS", "AJAX", "jQuery"]

    com_muitos = resultado_da(avaliacao(habilidades_desejaveis=muitos))
    com_um = resultado_da(avaliacao(habilidades_desejaveis=["PHP"]))

    assert com_muitos.nota < com_um.nota


def test_stack_principal_parcial_nao_recebe_nota_de_compatibilidade_total():
    resultado = resultado_da(
        avaliacao(habilidades_principais=["SQL", "C#", "JavaScript"]),
        perfil(habilidades=["Python", "Sprint Boot", "Django", "SQL", "Java"]),
    )

    assert resultado.nota == 73


def test_stack_principal_usa_as_mesmas_habilidades_na_nota_e_na_explicacao():
    resultado = resultado_da(
        avaliacao(habilidades_principais=["SQL", "C#", "JavaScript"]),
        perfil(habilidades=["Python", "Sprint Boot", "Django", "SQL", "Java"]),
    )

    assert resultado.requisitos_atendidos == ["SQL"]
    assert resultado.requisitos_nao_atendidos == ["C#", "JavaScript"]
    assert resultado.requisitos_tecnicos_analisados
    assert resultado.pontos_a_favor == []
    assert resultado.pontos_contra == []


def test_java_nao_corresponde_a_javascript():
    sem_correspondencia = resultado_da(avaliacao(habilidades_desejaveis=["JavaScript"]))
    com_correspondencia = resultado_da(
        avaliacao(habilidades_desejaveis=["JavaScript"]), perfil(habilidades=["JavaScript"])
    )

    assert sem_correspondencia.nota == 73
    assert com_correspondencia.nota == 98


def test_idiomas_e_pacote_office_nao_contam_na_nota_mas_aparecem_na_lista():
    resultado = resultado_da(
        avaliacao(habilidades_obrigatorias=["Inglês avançado", "Excel", "Python"])
    )

    assert resultado.nota == 98
    assert resultado.requisitos_atendidos == ["Python"]
    assert resultado.requisitos_nao_atendidos == ["Inglês avançado", "Excel"]


def test_vaga_que_so_pede_idiomas_e_office_e_tratada_como_sem_stack():
    so_genericos = resultado_da(
        avaliacao(habilidades_obrigatorias=["Inglês", "Word", "PowerPoint"])
    )
    sem_stack = resultado_da(avaliacao())

    assert so_genericos.nota == sem_stack.nota


def test_wordpress_nao_e_confundido_com_word():
    resultado = resultado_da(avaliacao(habilidades_obrigatorias=["WordPress", "PHP"]))

    assert resultado.nota == 64


def test_vaga_sem_stack_declarada_recebe_cobertura_neutra():
    resultado = resultado_da(avaliacao())

    assert resultado.nota == 73


def test_c_nao_corresponde_a_csharp_nem_a_cpp():
    resultado = resultado_da(
        avaliacao(habilidades_desejaveis=["C#", "C++"]), perfil(habilidades=["C"])
    )

    assert resultado.nota == 64


def test_csharp_por_extenso_corresponde_ao_simbolo():
    resultado = resultado_da(
        avaliacao(habilidades_desejaveis=["C#", "C++"]), perfil(habilidades=["CSharp", "CPP"])
    )

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
            habilidades_obrigatorias=["Python", "Java"],
            habilidades_desejaveis=["SQL"],
        )
    )

    assert resultado.nota == 93


def test_habilidade_obrigatoria_ausente_reduz_a_nota_sem_vetar():
    resultado = resultado_da(
        avaliacao(habilidades_obrigatorias=["Python", "C#"]),
        perfil(habilidades=["Python"]),
    )

    assert resultado.nota == 81


def test_stack_principal_parcial_reduz_a_nota_proporcionalmente():
    resultado = resultado_da(
        avaliacao(
            habilidades_obrigatorias=["Python"],
            habilidades_principais=["C#", "JavaScript", "SQL"],
        ),
        perfil(habilidades=["Python", "SQL"]),
    )

    assert resultado.nota == 90


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
