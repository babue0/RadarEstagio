from datetime import UTC, datetime

import pytest

from radar.domain.models import Modalidade, Perfil, Vaga
from radar.filtering.prefiltro import (
    exige_anos_de_experiencia,
    exige_senioridade,
    filtrar,
    fora_da_area_de_tecnologia,
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
    "titulo",
    [
        "Estágio em Técnico em Eletrônica",
        "Estagiário de Engenharia Mecânica",
        "Estágio Financeiro - Novo Hamburgo/RS",
        "Estagio Jurídico",
        "Estágio RH - Dados",
        "ESTÁGIO SUPERIOR - ENGENHARIA DE MANUFATURA",
        "Estágio em Comércio Exterior, Processos e Tecnologia",
        "Estagiário(a) em Pré-Venda de Soluções de TI",
        "Estagiário De Farmácia - Suporte E Desenvolvimento",
        "Estagiário(a) de Treinamento e Desenvolvimento",
        "Estagiário de R&S",
        "Estagiário(a) de People & Culture (People Analytics)",
        "Estágio em CRM | Digital",
        "Estágio em Turismo - 619",
    ],
)
def test_descarta_titulo_de_outra_area(titulo: str):
    assert fora_da_area_de_tecnologia(vaga(titulo=titulo))


@pytest.mark.parametrize(
    "titulo",
    [
        "Estágio em Desenvolvimento de Software",
        "Estágio em Ciência de Dados",
        "Estagiário de TI - Suporte e Redes",
        "Estágio - Engenharia de Software",
        "Estágio em Engenharia da Computação",
    ],
)
def test_mantem_titulo_de_computacao(titulo: str):
    assert not fora_da_area_de_tecnologia(vaga(titulo=titulo))


@pytest.mark.parametrize(
    "titulo",
    [
        "Estagiário(a) de T.I.",
        "Estágio em Ti - Infraestrutura",
        "Estagiário DevOps",
        "Estágio | Redes de Computadores, Sistemas de Informação",
        "Estágio Python",
    ],
)
def test_reconhece_area_de_tecnologia_no_titulo(titulo: str):
    assert not fora_da_area_de_tecnologia(vaga(titulo=titulo, descricao="Sem detalhes."))


@pytest.mark.parametrize(
    "titulo",
    [
        "Estagiário",
        "Programa de Estágio 2026.2",
        "Estágio de Hotelaria",
        "Estagiário de Endomarketing",
        "Estágio em Turismo",
    ],
)
def test_descarta_titulo_generico_sem_tecnologia_na_descricao(titulo: str):
    descricao = "Vaga para estudantes. Auxiliar a equipe nas rotinas do setor."
    assert fora_da_area_de_tecnologia(vaga(titulo=titulo, descricao=descricao))


@pytest.mark.parametrize(
    "descricao",
    [
        "Buscamos estudantes de Ciência da Computação ou Sistemas de Informação.",
        "Atuar no desenvolvimento de software em Python.",
        "Apoiar o time de suporte técnico e help desk.",
        "Conhecimento em banco de dados e SQL.",
    ],
)
def test_mantem_titulo_generico_quando_descricao_e_de_tecnologia(descricao: str):
    assert not fora_da_area_de_tecnologia(vaga(titulo="Programa de Estágio", descricao=descricao))


def test_titulo_de_outra_area_e_descartado_mesmo_com_descricao_de_tecnologia():
    descricao = "Desejável conhecimento em programação em Python."
    assert fora_da_area_de_tecnologia(vaga(titulo="Estágio em Eletrônica", descricao=descricao))


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


@pytest.mark.parametrize(
    "localizacao",
    ["Salvador, Bahia", "Niterói, Rio de Janeiro", "Campinas, Estado de São Paulo", "Brasil"],
)
def test_presencial_descarta_vaga_em_outra_cidade(localizacao: str):
    presencial = perfil(modalidade=Modalidade.PRESENCIAL, cidade="Rio de Janeiro, RJ")
    assert localizacao_incompativel(vaga(localizacao=localizacao), presencial)


@pytest.mark.parametrize(
    "localizacao",
    ["Rio de Janeiro, Estado do Rio de Janeiro", "rio de janeiro", "RIO DE JANEIRO, RJ"],
)
def test_presencial_compara_apenas_a_cidade_ignorando_acentos_e_caixa(localizacao: str):
    presencial = perfil(modalidade=Modalidade.PRESENCIAL, cidade="Rio de Janeiro, RJ")
    assert not localizacao_incompativel(vaga(localizacao=localizacao), presencial)


@pytest.mark.parametrize(
    "descricao",
    [
        "Trabalho 100% remoto.",
        "Regime de home office.",
        "Fully remote position.",
        "Prestar suporte técnico presencial e remoto aos usuários.",
    ],
)
def test_presencial_descarta_vaga_de_outra_cidade_mesmo_com_texto_remoto(descricao: str):
    presencial = perfil(modalidade=Modalidade.PRESENCIAL, cidade="Rio de Janeiro, RJ")
    vaga_fora = vaga(localizacao="São Paulo, Estado de São Paulo", descricao=descricao)
    assert localizacao_incompativel(vaga_fora, presencial)


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


def test_presencial_descarta_vaga_marcada_como_remota_pela_fonte_em_outra_cidade():
    presencial = perfil(modalidade=Modalidade.PRESENCIAL, cidade="Rio de Janeiro, RJ")
    vaga_remota = vaga(localizacao="Salvador, Bahia", modalidade=Modalidade.REMOTO)
    assert localizacao_incompativel(vaga_remota, presencial)


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
    primeira = vaga(titulo="Estágio em TI A")
    segunda = vaga(titulo="Estágio em TI B")

    assert filtrar([], perfil()) == []
    assert filtrar([segunda, primeira], perfil()) == [segunda, primeira]
