from datetime import UTC, datetime

from radar.domain.models import Modalidade, Perfil, ResultadoMatch, Vaga
from radar.matching.regras import aplicar_regras_objetivas


def vaga(modalidade: Modalidade | None) -> Vaga:
    return Vaga(
        id_externo="1",
        fonte="adzuna",
        titulo="Estágio em Data Science",
        empresa="Visagio",
        localizacao="Rio de Janeiro",
        descricao="Python e SQL desejável",
        url="https://exemplo.com/vaga/1",
        publicada_em=datetime(2026, 8, 28, tzinfo=UTC),
        modalidade=modalidade,
    )


def perfil(modalidade: Modalidade = Modalidade.REMOTO) -> Perfil:
    return Perfil(
        curso="Engenharia de Software",
        periodo=4,
        habilidades=["Python"],
        cidade="Rio de Janeiro, RJ",
        modalidade=modalidade,
    )


def test_limita_nota_sem_modalidade_e_preserva_apenas_lacunas_semanticas():
    original = ResultadoMatch(
        vaga=vaga(None),
        nota=95,
        pontos_contra=["Modalidade não informada", "SQL não informado"],
    )

    corrigido = aplicar_regras_objetivas([original], perfil())[0]

    assert corrigido.nota == 85
    assert corrigido.pontos_contra == ["SQL não informado"]
    assert corrigido.avisos_objetivos == ["Nota limitada a 85: modalidade não informada"]
    assert original.nota == 95
    assert original.pontos_contra == ["Modalidade não informada", "SQL não informado"]


def test_nao_cria_aviso_quando_nota_ja_respeita_o_limite():
    original = ResultadoMatch(
        vaga=vaga(None),
        nota=82,
        pontos_contra=["Modalidade não informada"],
    )

    corrigido = aplicar_regras_objetivas([original], perfil())[0]

    assert corrigido.nota == 82
    assert corrigido.pontos_contra == []
    assert corrigido.avisos_objetivos == []


def test_limita_modalidade_incompativel_para_perfil_remoto():
    original = ResultadoMatch(
        vaga=vaga(Modalidade.PRESENCIAL),
        nota=90,
        pontos_contra=["Vaga presencial", "SQL não informado"],
    )

    corrigido = aplicar_regras_objetivas([original], perfil())[0]

    assert corrigido.nota == 30
    assert corrigido.pontos_contra == ["SQL não informado"]
    assert corrigido.avisos_objetivos == ["Nota limitada a 30: modalidade incompatível"]


def test_mantem_resultado_quando_modalidade_e_compativel():
    original = ResultadoMatch(
        vaga=vaga(Modalidade.REMOTO),
        nota=95,
        pontos_contra=["SQL não informado"],
    )

    corrigido = aplicar_regras_objetivas([original], perfil())[0]

    assert corrigido.nota == 95
    assert corrigido.pontos_contra == ["SQL não informado"]
    assert corrigido.avisos_objetivos == []
