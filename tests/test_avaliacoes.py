from datetime import UTC, datetime

from radar.domain.models import AreaDeInteresse, ExtracaoDaVaga, Modalidade, Perfil, Vaga
from radar.matching.avaliacoes import pontuar


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


CURSO_ACEITO_DE_COMPUTACAO = "Ciência da Computação"
CURSO_ACEITO_DE_OUTRA_AREA = "Engenharia Elétrica"


def extracao(**alteracoes) -> ExtracaoDaVaga:
    dados = {
        "id_vaga": "vaga-1",
        "area_de_tecnologia": "compativel",
        "cursos_aceitos": [CURSO_ACEITO_DE_COMPUTACAO],
        "habilidades_obrigatorias": [],
        "habilidades_desejaveis": [],
    }
    dados.update(alteracoes)
    return ExtracaoDaVaga.model_validate(dados)


def resultado_da(extracao_da_vaga: ExtracaoDaVaga, candidato: Perfil | None = None):
    return pontuar(vaga(), extracao_da_vaga, candidato or perfil())


def test_stack_desejavel_sem_correspondencia_recebe_nota_baixa():
    requisitos = ["PHP", "MySQL", "SQL", "HTML5", "JavaScript", "REST", "VueJS", "AJAX", "jQuery"]

    resultado = resultado_da(extracao(habilidades_desejaveis=requisitos))

    assert resultado.nota == 57


def test_muitos_requisitos_ausentes_pesam_mais_que_um_so():
    muitos = ["PHP", "MySQL", "HTML5", "VueJS", "AJAX", "jQuery"]

    com_muitos = resultado_da(extracao(habilidades_desejaveis=muitos))
    com_um = resultado_da(extracao(habilidades_desejaveis=["PHP"]))

    assert com_muitos.nota < com_um.nota


def test_stack_principal_parcial_nao_recebe_nota_de_compatibilidade_total():
    resultado = resultado_da(
        extracao(habilidades_principais=["SQL", "C#", "JavaScript"]),
        perfil(habilidades=["Python", "Sprint Boot", "Django", "SQL", "Java"]),
    )

    assert resultado.nota == 75


def test_stack_principal_usa_as_mesmas_habilidades_na_nota_e_na_explicacao():
    resultado = resultado_da(
        extracao(habilidades_principais=["SQL", "C#", "JavaScript"]),
        perfil(habilidades=["Python", "Sprint Boot", "Django", "SQL", "Java"]),
    )

    assert resultado.requisitos_atendidos == ["SQL"]
    assert resultado.requisitos_nao_atendidos == ["C#", "JavaScript"]
    assert resultado.requisitos_tecnicos_analisados
    assert resultado.pontos_a_favor == ["Curso compatível"]
    assert resultado.pontos_contra == []


def test_java_nao_corresponde_a_javascript():
    sem_correspondencia = resultado_da(extracao(habilidades_desejaveis=["JavaScript"]))
    com_correspondencia = resultado_da(
        extracao(habilidades_desejaveis=["JavaScript"]), perfil(habilidades=["JavaScript"])
    )

    assert sem_correspondencia.nota == 75
    assert com_correspondencia.nota == 98


def test_idiomas_e_pacote_office_nao_contam_na_nota_mas_aparecem_na_lista():
    resultado = resultado_da(
        extracao(habilidades_obrigatorias=["Inglês avançado", "Excel", "Python"])
    )

    assert resultado.nota == 98
    assert resultado.requisitos_atendidos == ["Python"]
    assert resultado.requisitos_nao_atendidos == ["Inglês avançado", "Excel"]


def test_vaga_que_so_pede_idiomas_e_office_e_tratada_como_sem_stack():
    so_genericos = resultado_da(extracao(habilidades_obrigatorias=["Inglês", "Word", "PowerPoint"]))
    sem_stack = resultado_da(extracao())

    assert so_genericos.nota == sem_stack.nota


def test_wordpress_nao_e_confundido_com_word():
    resultado = resultado_da(extracao(habilidades_obrigatorias=["WordPress", "PHP"]))

    assert resultado.nota == 68


def test_vaga_sem_stack_declarada_recebe_cobertura_neutra():
    resultado = resultado_da(extracao())

    assert resultado.nota == 68


def test_vaga_da_area_de_interesse_ganha_o_peso_cheio():
    perfil_web = perfil(habilidades=["Python", "Java"])
    perfil_web.areas_de_interesse = [AreaDeInteresse.DESENVOLVIMENTO_WEB]

    resultado = resultado_da(
        extracao(areas_da_vaga=["desenvolvimento_web", "dados_ia"]), perfil_web
    )

    assert resultado.nota == 68
    assert resultado.avisos_objetivos == []


def test_vaga_fora_da_area_de_interesse_perde_o_fator_e_ganha_aviso():
    perfil_web = perfil(habilidades=["Python", "Java"])
    perfil_web.areas_de_interesse = [AreaDeInteresse.DESENVOLVIMENTO_WEB]

    resultado = resultado_da(extracao(areas_da_vaga=["infraestrutura_redes"]), perfil_web)

    assert resultado.nota == 58
    assert resultado.avisos_objetivos == ["Fora das suas áreas de interesse"]


def test_vaga_sem_area_reconhecida_fica_neutra_para_quem_tem_interesses():
    perfil_web = perfil(habilidades=["Python", "Java"])
    perfil_web.areas_de_interesse = [AreaDeInteresse.DESENVOLVIMENTO_WEB]

    resultado = resultado_da(extracao(areas_da_vaga=["area_inventada"]), perfil_web)

    assert resultado.nota == 63
    assert resultado.avisos_objetivos == []


def test_vaga_sem_area_reconhecida_tambem_respeita_o_teto_de_65():
    perfil_web = perfil(habilidades=["SQL"])
    perfil_web.areas_de_interesse = [AreaDeInteresse.DESENVOLVIMENTO_WEB]

    resultado = resultado_da(
        extracao(habilidades_obrigatorias=["SQL"], areas_da_vaga=[]), perfil_web
    )

    assert resultado.nota == 65
    assert resultado.avisos_objetivos == []


def test_match_total_de_habilidades_fora_do_interesse_fica_limitado_a_65():
    perfil_web = perfil(habilidades=["SQL"])
    perfil_web.areas_de_interesse = [AreaDeInteresse.DESENVOLVIMENTO_WEB]

    resultado = resultado_da(
        extracao(habilidades_obrigatorias=["SQL"], areas_da_vaga=["infraestrutura_redes"]),
        perfil_web,
    )

    assert resultado.nota == 65
    assert resultado.avisos_objetivos == ["Fora das suas áreas de interesse"]


def test_perfil_sem_interesses_nao_e_penalizado_por_area_da_vaga():
    resultado = resultado_da(extracao(areas_da_vaga=["infraestrutura_redes"]))

    assert resultado.nota == 68
    assert resultado.avisos_objetivos == []


def test_vaga_sem_stack_nao_supera_vaga_detalhada_e_meio_compativel():
    sem_stack = resultado_da(extracao())
    detalhada = resultado_da(
        extracao(habilidades_principais=["Python", "SQL", "Git"]),
        perfil(habilidades=["Python", "Git"]),
    )

    assert detalhada.nota > sem_stack.nota


def test_c_nao_corresponde_a_csharp_nem_a_cpp():
    resultado = resultado_da(
        extracao(habilidades_desejaveis=["C#", "C++"]), perfil(habilidades=["C"])
    )

    assert resultado.nota == 68


def test_csharp_por_extenso_corresponde_ao_simbolo():
    resultado = resultado_da(
        extracao(habilidades_desejaveis=["C#", "C++"]), perfil(habilidades=["CSharp", "CPP"])
    )

    assert resultado.nota == 98


def test_alias_js_corresponde_a_javascript():
    resultado = resultado_da(
        extracao(habilidades_desejaveis=["JavaScript"]), perfil(habilidades=["JS"])
    )

    assert resultado.nota == 98


def test_cobertura_total_da_stack_desejavel_recebe_98_pontos():
    resultado = resultado_da(extracao(habilidades_desejaveis=["Python", "Java"]))

    assert resultado.nota == 98


def test_obrigatorias_valem_oitenta_porcento_quando_ha_desejaveis():
    resultado = resultado_da(
        extracao(
            habilidades_obrigatorias=["Python", "Java"],
            habilidades_desejaveis=["SQL"],
        )
    )

    assert resultado.nota == 93


def test_habilidade_obrigatoria_ausente_reduz_a_nota_sem_vetar():
    resultado = resultado_da(
        extracao(habilidades_obrigatorias=["Python", "C#"]),
        perfil(habilidades=["Python"]),
    )

    assert resultado.nota == 83


def test_stack_principal_parcial_reduz_a_nota_proporcionalmente():
    resultado = resultado_da(
        extracao(
            habilidades_obrigatorias=["Python"],
            habilidades_principais=["C#", "JavaScript", "SQL"],
        ),
        perfil(habilidades=["Python", "SQL"]),
    )

    assert resultado.nota == 91


def test_curso_incompativel_limita_a_nota_a_35_com_aviso():
    resultado = resultado_da(
        extracao(
            cursos_aceitos=[CURSO_ACEITO_DE_OUTRA_AREA], habilidades_obrigatorias=["Python", "Java"]
        )
    )

    assert resultado.nota == 35
    assert "Exige formação de outra área" in resultado.avisos_objetivos


def test_curso_parcial_limita_a_nota_a_75():
    resultado = resultado_da(
        extracao(cursos_aceitos=[], habilidades_obrigatorias=["Python", "Java"])
    )

    assert resultado.nota == 75
    assert resultado.avisos_objetivos == []


def test_fatores_parciais_recebem_metade_do_peso():
    resultado = resultado_da(
        extracao(
            area_de_tecnologia="parcial",
            cursos_aceitos=[],
            experiencia_desejavel=True,
            habilidades_obrigatorias=["Python"],
        )
    )

    assert resultado.nota == 75


def test_habilidade_nao_vira_ponto_porque_ja_aparece_na_lista_de_requisitos():
    resultado = resultado_da(
        extracao(habilidades_obrigatorias=["Python"], cursos_aceitos=[]),
        perfil(habilidades=["Python"]),
    )

    assert resultado.requisitos_atendidos == ["Python"]
    assert resultado.pontos_a_favor == []
    assert resultado.pontos_contra == []


def test_periodo_minimo_acima_do_perfil_vira_ponto_contra():
    resultado = resultado_da(extracao(periodo_minimo=8))

    assert resultado.pontos_contra == ["Período mínimo incompatível"]


def test_experiencia_exigida_vira_ponto_contra_no_lugar_do_periodo():
    resultado = resultado_da(extracao(periodo_minimo=8, experiencia_minima_anos=2))

    assert resultado.pontos_contra == ["Exige experiência prévia"]
