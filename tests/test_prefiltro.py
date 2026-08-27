from datetime import UTC, datetime

import pytest

from radar.domain.models import Modalidade, Perfil, Vaga
from radar.filtering.prefiltro import (
    exige_anos_de_experiencia,
    exige_senioridade,
    filtrar,
    localizacao_incompativel,
    modalidade_incompativel,
    nao_e_estagio,
)


def vaga(
    titulo: str = "Estágio em Desenvolvimento",
    descricao: str = "Vaga de estágio para estudantes de tecnologia.",
    localizacao: str = "Rio de Janeiro, Rio de Janeiro",
    modalidade: Modalidade | None = None,
) -> Vaga:
    return Vaga(
        id_externo="1",
        fonte="adzuna",
        titulo=titulo,
        empresa="Empresa Exemplo",
        localizacao=localizacao,
        descricao=descricao,
        url="https://exemplo.com/vaga/1",
        publicada_em=datetime(2026, 8, 25, tzinfo=UTC),
        modalidade=modalidade,
    )


def perfil(
    modalidade: Modalidade = Modalidade.REMOTO, cidade: str = "Rio de Janeiro, RJ"
) -> Perfil:
    return Perfil(
        curso="Engenharia de Software",
        periodo=4,
        habilidades=["Python"],
        cidade=cidade,
        modalidade=modalidade,
    )


@pytest.mark.parametrize(
    "titulo",
    [
        "Estágio em TI",
        "ESTAGIO - CURSO TECNOLOGIA",
        "Estagiário de TI",
        "Estagiária de Dados",
        "Software Engineering Intern",
        "Internship - Data Science",
    ],
)
def test_reconhece_estagio_no_titulo_com_e_sem_acento(titulo: str):
    assert not nao_e_estagio(vaga(titulo=titulo))


@pytest.mark.parametrize(
    "titulo",
    [
        "Analista Suporte Técnico",
        "Preceptor - Fisioterapia - Estácio Angra Dos Reis",
        "Analista de Internet",
        "International Sales Analyst",
    ],
)
def test_descarta_titulo_que_nao_e_estagio(titulo: str):
    assert nao_e_estagio(vaga(titulo=titulo))


@pytest.mark.parametrize(
    "titulo",
    [
        "Desenvolvedor Pleno",
        "Analista Sênior",
        "Analista Senior",
        "Especialista em Dados",
        "Coordenador de TI",
        "Estagiário Pleno",
    ],
)
def test_descarta_senioridade_no_titulo(titulo: str):
    assert exige_senioridade(vaga(titulo=titulo))


def test_senioridade_apenas_na_descricao_nao_descarta():
    descricao = "O estagiário reportará ao coordenador de TI e apoiará os especialistas."
    assert not exige_senioridade(vaga(descricao=descricao))


@pytest.mark.parametrize(
    "descricao",
    [
        "Requisito: 2 anos de experiência com Python.",
        "Experiência mínima de 3 anos.",
        "5+ anos de experiencia em suporte técnico",
        "Experiência de 2 anos em redes",
    ],
)
def test_descarta_exigencia_de_dois_ou_mais_anos_de_experiencia(descricao: str):
    assert exige_anos_de_experiencia(vaga(descricao=descricao))


@pytest.mark.parametrize(
    "descricao",
    [
        "Não exige experiência.",
        "1 ano de experiência é desejável.",
        "Empresa com 20 anos de experiência no mercado.",
        "Experiência com Python é um diferencial.",
    ],
)
def test_mantem_vaga_sem_exigencia_de_experiencia(descricao: str):
    assert not exige_anos_de_experiencia(vaga(descricao=descricao))


@pytest.mark.parametrize(
    "modalidade", [Modalidade.REMOTO, Modalidade.HIBRIDO, Modalidade.INDIFERENTE]
)
def test_localizacao_so_e_avaliada_para_perfil_presencial(modalidade: Modalidade):
    vaga_em_outra_cidade = vaga(localizacao="Salvador, Bahia")
    assert not localizacao_incompativel(vaga_em_outra_cidade, perfil(modalidade=modalidade))


def test_presencial_mantem_vaga_na_mesma_cidade():
    presencial = perfil(modalidade=Modalidade.PRESENCIAL, cidade="Rio de Janeiro, RJ")
    vaga_no_rio = vaga(localizacao="Rio de Janeiro, Rio de Janeiro")
    assert not localizacao_incompativel(vaga_no_rio, presencial)


def test_presencial_descarta_vaga_em_outra_cidade():
    presencial = perfil(modalidade=Modalidade.PRESENCIAL, cidade="Rio de Janeiro, RJ")
    assert localizacao_incompativel(vaga(localizacao="Salvador, Bahia"), presencial)


@pytest.mark.parametrize(
    "descricao", ["Trabalho 100% remoto.", "Regime de home office.", "Fully remote position."]
)
def test_presencial_mantem_vaga_remota_de_outra_cidade(descricao: str):
    presencial = perfil(modalidade=Modalidade.PRESENCIAL, cidade="Rio de Janeiro, RJ")
    vaga_remota = vaga(localizacao="Salvador, Bahia", descricao=descricao)
    assert not localizacao_incompativel(vaga_remota, presencial)


@pytest.mark.parametrize(
    "modalidade", [Modalidade.PRESENCIAL, Modalidade.HIBRIDO, Modalidade.INDIFERENTE]
)
def test_modalidade_so_e_avaliada_para_perfil_remoto(modalidade: Modalidade):
    vaga_presencial = vaga(descricao="Trabalho presencial na sede.")
    assert not modalidade_incompativel(vaga_presencial, perfil(modalidade=modalidade))


@pytest.mark.parametrize(
    "descricao",
    [
        "Trabalho presencial na sede.",
        "Atuação presencialmente em São Paulo.",
        "Modelo híbrido, 3 dias no escritório.",
        "Hybrid work model.",
        "On-site position.",
    ],
)
def test_remoto_descarta_vaga_presencial_ou_hibrida(descricao: str):
    assert modalidade_incompativel(vaga(descricao=descricao), perfil(modalidade=Modalidade.REMOTO))


@pytest.mark.parametrize(
    "descricao",
    ["Trabalho 100% remoto.", "Regime de home office.", "Fully remote position."],
)
def test_remoto_mantem_vaga_remota_de_qualquer_lugar(descricao: str):
    vaga_remota = vaga(localizacao="Lisboa, Portugal", descricao=descricao)
    assert not modalidade_incompativel(vaga_remota, perfil(modalidade=Modalidade.REMOTO))


@pytest.mark.parametrize("modalidade", [Modalidade.PRESENCIAL, Modalidade.HIBRIDO])
def test_remoto_descarta_pela_modalidade_informada_pela_fonte(modalidade: Modalidade):
    vaga_com_texto_remoto = vaga(descricao="Trabalho remoto.", modalidade=modalidade)
    assert modalidade_incompativel(vaga_com_texto_remoto, perfil(modalidade=Modalidade.REMOTO))


def test_remoto_mantem_vaga_marcada_como_remota_pela_fonte_mesmo_com_texto_presencial():
    vaga_remota = vaga(descricao="Escritório presencial em SP.", modalidade=Modalidade.REMOTO)
    assert not modalidade_incompativel(vaga_remota, perfil(modalidade=Modalidade.REMOTO))


def test_presencial_mantem_vaga_marcada_como_remota_pela_fonte_em_outra_cidade():
    presencial = perfil(modalidade=Modalidade.PRESENCIAL, cidade="Rio de Janeiro, RJ")
    vaga_remota = vaga(localizacao="Salvador, Bahia", modalidade=Modalidade.REMOTO)
    assert not localizacao_incompativel(vaga_remota, presencial)


def test_remoto_mantem_vaga_sem_modalidade_informada():
    sem_modalidade = vaga(localizacao="São Paulo, São Paulo", descricao="Vaga de estágio em TI.")
    assert not modalidade_incompativel(sem_modalidade, perfil(modalidade=Modalidade.REMOTO))


def test_remoto_mantem_vaga_que_menciona_presencial_e_remoto():
    ambigua = vaga(descricao="Presencial ou remoto, a combinar.")
    assert not modalidade_incompativel(ambigua, perfil(modalidade=Modalidade.REMOTO))


def test_filtrar_remove_apenas_vagas_com_motivo_de_descarte():
    limpa = vaga(titulo="Estágio em Desenvolvimento")
    nao_estagio = vaga(titulo="Analista de Suporte")
    com_senioridade = vaga(titulo="Estagiário Pleno")
    com_experiencia = vaga(titulo="Estágio em Dados", descricao="Mínimo 3 anos de experiência.")
    em_outra_cidade = vaga(titulo="Estágio em Redes", localizacao="Salvador, Bahia")
    presencial = perfil(modalidade=Modalidade.PRESENCIAL, cidade="Rio de Janeiro, RJ")

    resultado = filtrar(
        [nao_estagio, limpa, com_senioridade, com_experiencia, em_outra_cidade], presencial
    )

    assert resultado == [limpa]


def test_filtrar_para_perfil_remoto_remove_presencial_e_mantem_sem_modalidade():
    remota = vaga(titulo="Estágio Dev", localizacao="Lisboa, Portugal", descricao="100% remoto.")
    sem_modalidade = vaga(titulo="Estágio Dev", localizacao="São Paulo, São Paulo")
    presencial = vaga(titulo="Estágio Dev", descricao="Trabalho presencial.")

    resultado = filtrar([remota, sem_modalidade, presencial], perfil(modalidade=Modalidade.REMOTO))

    assert resultado == [remota, sem_modalidade]


def test_filtrar_preserva_ordem_e_aceita_lista_vazia():
    primeira = vaga(titulo="Estágio A")
    segunda = vaga(titulo="Estágio B")

    assert filtrar([], perfil()) == []
    assert filtrar([segunda, primeira], perfil()) == [segunda, primeira]
