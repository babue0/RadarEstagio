from radar.domain.models import ExtracaoDaVaga, Modalidade, NivelCompatibilidade, Perfil
from radar.matching.compatibilidade import derivar_niveis, montar_pontos


def perfil(curso: str = "Engenharia de Software", periodo: int = 4) -> Perfil:
    return Perfil(
        curso=curso,
        periodo=periodo,
        habilidades=["Python"],
        cidade="Rio de Janeiro, RJ",
        modalidade=Modalidade.PRESENCIAL,
    )


def extracao(**alteracoes) -> ExtracaoDaVaga:
    dados = {"id_vaga": "vaga-1", "area_de_tecnologia": "compativel"}
    dados.update(alteracoes)
    return ExtracaoDaVaga.model_validate(dados)


def curso_de(extracao_da_vaga: ExtracaoDaVaga, candidato: Perfil | None = None):
    return derivar_niveis(extracao_da_vaga, candidato or perfil()).curso


def periodo_de(extracao_da_vaga: ExtracaoDaVaga, candidato: Perfil | None = None):
    return derivar_niveis(extracao_da_vaga, candidato or perfil()).periodo_experiencia


def test_vaga_sem_curso_declarado_fica_parcial_em_vez_de_incompativel():
    assert curso_de(extracao(cursos_aceitos=[])) is NivelCompatibilidade.PARCIAL


def test_qualquer_curso_aceito_e_compativel():
    assert curso_de(extracao(aceita_qualquer_curso=True)) is NivelCompatibilidade.COMPATIVEL


def test_lista_com_algum_curso_de_computacao_e_compativel():
    aceitos = ["Administração", "Ciência da Computação"]

    assert curso_de(extracao(cursos_aceitos=aceitos)) is NivelCompatibilidade.COMPATIVEL


def test_curso_correlato_de_computacao_conta_mesmo_sem_ser_o_do_perfil():
    aceitos = ["Análise e Desenvolvimento de Sistemas"]

    assert curso_de(extracao(cursos_aceitos=aceitos)) is NivelCompatibilidade.COMPATIVEL


def test_lista_sem_curso_de_computacao_e_incompativel():
    aceitos = ["Engenharia Elétrica", "Engenharia Mecânica", "Administração"]

    assert curso_de(extracao(cursos_aceitos=aceitos)) is NivelCompatibilidade.INCOMPATIVEL


def test_curso_do_perfil_aceito_explicitamente_vale_mesmo_fora_do_catalogo():
    candidato = perfil(curso="Engenharia de Controle e Automação")
    aceitos = ["Engenharia de Controle e Automação"]

    assert curso_de(extracao(cursos_aceitos=aceitos), candidato) is (
        NivelCompatibilidade.COMPATIVEL
    )


def test_vaga_sem_exigencia_de_periodo_e_compativel():
    assert periodo_de(extracao()) is NivelCompatibilidade.COMPATIVEL


def test_periodo_minimo_atendido_e_compativel():
    assert periodo_de(extracao(periodo_minimo=4)) is NivelCompatibilidade.COMPATIVEL


def test_periodo_minimo_acima_do_perfil_e_incompativel():
    assert periodo_de(extracao(periodo_minimo=6)) is NivelCompatibilidade.INCOMPATIVEL


def test_experiencia_obrigatoria_e_incompativel():
    assert periodo_de(extracao(experiencia_minima_anos=1)) is NivelCompatibilidade.INCOMPATIVEL


def test_experiencia_apenas_desejavel_e_parcial():
    assert periodo_de(extracao(experiencia_desejavel=True)) is NivelCompatibilidade.PARCIAL


def test_area_de_tecnologia_vem_direto_da_vaga():
    niveis = derivar_niveis(extracao(area_de_tecnologia="incompativel"), perfil())

    assert niveis.area is NivelCompatibilidade.INCOMPATIVEL


def test_curso_compativel_sem_lista_declarada_nao_vira_ponto_a_favor():
    extracao_sem_curso = extracao(cursos_aceitos=[])
    niveis = derivar_niveis(extracao_sem_curso, perfil())

    a_favor, contra = montar_pontos(extracao_sem_curso, niveis)

    assert a_favor == []
    assert contra == []
