from datetime import UTC, datetime

from radar.domain.models import Modalidade, Vaga
from radar.filtering.duplicatas import chave_de_duplicata, mais_completa, remover_duplicatas


def vaga(
    titulo: str = "Estágio em Desenvolvimento",
    empresa: str = "Empresa Exemplo",
    fonte: str = "adzuna",
    descricao: str = "descrição",
    modalidade: Modalidade | None = None,
    numero: int = 1,
) -> Vaga:
    return Vaga(
        id_externo=str(numero),
        fonte=fonte,
        titulo=titulo,
        empresa=empresa,
        localizacao="Rio de Janeiro",
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
