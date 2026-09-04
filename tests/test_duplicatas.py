from datetime import UTC, datetime

from radar.domain.models import Modalidade, Vaga
from radar.filtering.duplicatas import (
    chave_de_duplicata,
    descricoes_semelhantes,
    mais_completa,
    remover_duplicatas,
    remover_republicacoes_de,
)


def vaga(
    titulo: str = "Estágio em Desenvolvimento",
    empresa: str = "Empresa Exemplo",
    fonte: str = "adzuna",
    descricao: str = "descrição",
    modalidade: Modalidade | None = None,
    numero: int = 1,
    localizacao: str = "Rio de Janeiro",
) -> Vaga:
    return Vaga(
        id_externo=str(numero),
        fonte=fonte,
        titulo=titulo,
        empresa=empresa,
        localizacao=localizacao,
        descricao=descricao,
        url=f"https://{fonte}.com/vaga/{numero}",
        publicada_em=datetime(2026, 8, 25, tzinfo=UTC),
        modalidade=modalidade,
    )


def test_chave_ignora_acentos_maiusculas_pontuacao_e_espacos_extras():
    assert chave_de_duplicata(vaga("Estágio - Desenvolvimento  ", "Empresa Exemplo ")) == (
        chave_de_duplicata(vaga("ESTAGIO DESENVOLVIMENTO", "empresa exemplo"))
    )


def test_chave_distingue_empresas_diferentes_com_o_mesmo_titulo():
    assert chave_de_duplicata(vaga(empresa="A")) != chave_de_duplicata(vaga(empresa="B"))


def test_mais_completa_prefere_quem_informa_modalidade():
    sem = vaga(descricao="descrição bem mais longa que a outra")
    com = vaga(fonte="gupy", descricao="curta", modalidade=Modalidade.REMOTO)

    assert mais_completa(sem, com) is com
    assert mais_completa(com, sem) is com


def test_mais_completa_desempata_pela_descricao_mais_longa():
    curta = vaga(descricao="curta")
    longa = vaga(fonte="gupy", descricao="descrição mais longa", numero=2)

    assert mais_completa(curta, longa) is longa
    assert mais_completa(longa, curta) is longa


def test_mais_completa_em_empate_total_mantem_a_primeira():
    primeira = vaga(numero=1)
    segunda = vaga(numero=2)

    assert mais_completa(primeira, segunda) is primeira


def test_remover_duplicatas_mantem_a_versao_mais_completa_na_posicao_original():
    adzuna = vaga(fonte="adzuna", numero=1)
    outra = vaga(titulo="Estágio em Dados", numero=2)
    gupy = vaga(fonte="gupy", modalidade=Modalidade.HIBRIDO, numero=3)

    resultado = remover_duplicatas([adzuna, outra, gupy])

    assert resultado == [gupy, outra]


def test_remover_duplicatas_preserva_lista_sem_repeticao():
    vagas = [vaga(numero=1), vaga(titulo="Estágio em Dados", numero=2)]

    assert remover_duplicatas(vagas) == vagas
    assert remover_duplicatas([]) == []


ANUNCIO = (
    "Dar apoio e suporte nas atividades de desenvolvimento das ferramentas no site. "
    "Requisitos: desejável conhecimento em PHP orientado a objeto, MySQL, SQL, HTML5, "
    "JavaScript e REST API. Necessário cursando graduação em Ciência da Computação."
)
ANUNCIO_COM_SALARIO = ANUNCIO.replace("Requisitos:", "1000,00")


def test_descricoes_quase_iguais_sao_semelhantes():
    assert descricoes_semelhantes(vaga(descricao=ANUNCIO), vaga(descricao=ANUNCIO_COM_SALARIO))


def test_descricoes_diferentes_nao_sao_semelhantes():
    outra = "Estágio em suporte de infraestrutura, redes e atendimento a usuários internos."
    assert not descricoes_semelhantes(vaga(descricao=ANUNCIO), vaga(descricao=outra))


def test_descricao_curta_nunca_e_semelhante():
    curta = "Vaga de estágio em TI. Envie seu currículo."
    assert not descricoes_semelhantes(vaga(descricao=""), vaga(descricao=""))
    assert not descricoes_semelhantes(vaga(descricao=curta), vaga(descricao=curta))


def test_remover_duplicatas_une_o_mesmo_anuncio_republicado_por_agregadores():
    original = vaga("Estágio em Programação", "BuscarVagas", descricao=ANUNCIO, numero=1)
    republicada = vaga("Estágio em Programação", "Divulga Vagas", descricao=ANUNCIO, numero=2)
    com_salario = vaga(
        "Estágio em Programação",
        "Divulga Vagas - Consultoria",
        descricao=ANUNCIO_COM_SALARIO,
        numero=3,
    )

    assert remover_duplicatas([original, republicada, com_salario]) == [original]


def test_descricao_truncada_pela_fonte_com_final_diferente_ainda_e_semelhante():
    cabecalho = (
        ANUNCIO + " Desejável também noções de Git, Docker e metodologias ágeis no dia a dia."
    )
    completa = cabecalho + " Benefícios: vale transporte, refeição no local e bolsa auxílio."
    truncada = cabecalho + " Horário: segunda a sexta, das 9h às 15h, na Barra da"
    assert descricoes_semelhantes(vaga(descricao=completa), vaga(descricao=truncada))


def test_remover_duplicatas_ignora_sufixo_de_agregador_no_titulo():
    original = vaga(
        "Estagiário de TI - São Gonçalo - RJ", "BuscarVagas", descricao=ANUNCIO, numero=1
    )
    com_sufixo = vaga(
        "Estagiário de TI - São Gonçalo - RJ - Vaga", "Divulga Vagas", descricao=ANUNCIO, numero=2
    )

    assert remover_duplicatas([original, com_sufixo]) == [original]


def test_remover_duplicatas_mantem_mesmo_titulo_em_cidades_diferentes():
    rio = vaga("Estágio em Programação", "A", descricao=ANUNCIO, numero=1)
    salvador = vaga(
        "Estágio em Programação", "B", descricao=ANUNCIO, numero=2, localizacao="Salvador, Bahia"
    )

    assert remover_duplicatas([rio, salvador]) == [rio, salvador]


def test_remover_duplicatas_mantem_mesmo_titulo_com_descricoes_diferentes():
    primeira = vaga("Estágio em TI", "A", descricao=ANUNCIO, numero=1)
    segunda = vaga(
        "Estágio em TI", "B", descricao="Suporte a usuários e manutenção de redes.", numero=2
    )

    assert remover_duplicatas([primeira, segunda]) == [primeira, segunda]


def test_remover_republicacoes_de_descarta_anuncio_igual_ao_ja_conhecido():
    enviada = vaga("Estagio Programador - Rio de Janeiro - Rj", "Divulga Vagas", descricao=ANUNCIO)
    republicada = vaga(
        "Estagio Programador - Rio de Janeiro - Rj - Vaga",
        "BuscarVagas",
        descricao=ANUNCIO_COM_SALARIO,
        numero=2,
    )
    inedita = vaga("Estágio em Dados", "Outra Empresa", descricao=ANUNCIO, numero=3)

    assert remover_republicacoes_de([republicada, inedita], [enviada]) == [inedita]


def test_remover_republicacoes_de_mantem_mesmo_titulo_com_descricao_diferente():
    enviada = vaga("Estágio em TI", "A", descricao=ANUNCIO)
    outra = vaga(
        "Estágio em TI",
        "B",
        descricao="Suporte a usuários, manutenção de redes e atendimento interno na sede.",
        numero=2,
    )

    assert remover_republicacoes_de([outra], [enviada]) == [outra]


def test_remover_republicacoes_de_sem_conhecidas_mantem_tudo():
    candidatas = [vaga("Estágio em TI", "A", descricao=ANUNCIO)]

    assert remover_republicacoes_de(candidatas, []) == candidatas
