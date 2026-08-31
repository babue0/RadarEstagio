from datetime import UTC, date, datetime

from radar.domain.models import Modalidade, ResultadoMatch, Vaga
from radar.notification.formatador import (
    LIMITE_DE_CARACTERES_DO_TELEGRAM,
    dividir_em_mensagens,
    formatar_mensagem,
)

DATA_DE_TESTE = date(2026, 8, 26)


def vaga(titulo: str = "Estágio Python", numero: int = 1) -> Vaga:
    return Vaga(
        id_externo=str(numero),
        fonte="adzuna",
        titulo=titulo,
        empresa="Empresa Exemplo",
        localizacao="Rio de Janeiro",
        descricao="descrição",
        url=f"https://exemplo.com/vaga/{numero}",
        publicada_em=datetime(2026, 8, 25, tzinfo=UTC),
    )


def resultado(
    nota: int,
    titulo: str = "Estágio Python",
    alerta: str | None = None,
    numero: int = 1,
    a_favor: list[str] | None = None,
    contra: list[str] | None = None,
    avisos: list[str] | None = None,
    requisitos_atendidos: list[str] | None = None,
    requisitos_nao_atendidos: list[str] | None = None,
    requisitos_analisados: bool = False,
) -> ResultadoMatch:
    return ResultadoMatch(
        vaga=vaga(titulo, numero),
        nota=nota,
        pontos_a_favor=["Python"] if a_favor is None else a_favor,
        pontos_contra=["Exige Java"] if contra is None else contra,
        avisos_objetivos=[] if avisos is None else avisos,
        requisitos_atendidos=[] if requisitos_atendidos is None else requisitos_atendidos,
        requisitos_nao_atendidos=(
            [] if requisitos_nao_atendidos is None else requisitos_nao_atendidos
        ),
        requisitos_tecnicos_analisados=requisitos_analisados,
        alerta_pegadinha=alerta,
    )


def test_cabecalho_contem_a_data():
    texto = formatar_mensagem([resultado(50)], DATA_DE_TESTE)

    assert texto.startswith("📡 <b>Radar de Estágio</b> — 26/08/2026")


def test_lista_vazia_gera_mensagem_de_nenhuma_vaga():
    texto = formatar_mensagem([], DATA_DE_TESTE)

    assert "26/08/2026" in texto
    assert "Nenhuma vaga compatível" in texto


def test_ordena_por_nota_decrescente_e_numera():
    texto = formatar_mensagem(
        [
            resultado(40, "Baixa", numero=1),
            resultado(90, "Alta", numero=2),
            resultado(70, "Média", numero=3),
        ],
        DATA_DE_TESTE,
    )

    assert texto.index("1. Alta") < texto.index("2. Média") < texto.index("3. Baixa")


def test_inclui_titulo_empresa_nota_pontos_e_link():
    texto = formatar_mensagem(
        [resultado(85, a_favor=["Python", "SQL"], contra=["Presencial em SP"])], DATA_DE_TESTE
    )

    assert "Estágio Python" in texto
    assert "Empresa Exemplo" in texto
    assert "Nota 85/100" in texto
    assert "✅ Python · SQL" in texto
    assert "❌ Presencial em SP" in texto
    assert '<a href="https://exemplo.com/vaga/1">' in texto


def test_exibe_requisitos_tecnicos_atendidos_e_nao_atendidos_explicitamente():
    texto = formatar_mensagem(
        [
            resultado(
                64,
                a_favor=[],
                contra=[],
                requisitos_atendidos=["SQL"],
                requisitos_nao_atendidos=["C#", "JavaScript"],
                requisitos_analisados=True,
            )
        ],
        DATA_DE_TESTE,
    )

    assert "✅ <b>Requisitos atendidos:</b> SQL" in texto
    assert "❌ <b>Requisitos não atendidos:</b> C# · JavaScript" in texto


def test_avisa_quando_descricao_nao_informa_requisitos_tecnicos():
    texto = formatar_mensagem(
        [resultado(73, a_favor=[], contra=[], requisitos_analisados=True)], DATA_DE_TESTE
    )

    assert "ℹ️ <b>Requisitos técnicos:</b> não informados na descrição" in texto


def test_descricao_incompleta_nao_afirma_que_requisitos_nao_foram_informados():
    resultado_incompleto = resultado(
        60,
        a_favor=[],
        contra=[],
        requisitos_analisados=True,
        avisos=["Descrição incompleta: requisitos podem estar ausentes; nota limitada a 60"],
    )
    resultado_incompleto = resultado_incompleto.model_copy(
        update={"vaga": resultado_incompleto.vaga.model_copy(update={"descricao_completa": False})}
    )

    texto = formatar_mensagem([resultado_incompleto], DATA_DE_TESTE)

    assert "requisitos podem estar ausentes" in texto
    assert "não informados na descrição" not in texto


def test_inclui_localizacao_modalidade_fonte_e_data_de_publicacao():
    oportunidade = vaga().model_copy(update={"modalidade": Modalidade.HIBRIDO})
    texto = formatar_mensagem(
        [resultado(85).model_copy(update={"vaga": oportunidade})], DATA_DE_TESTE
    )

    assert "📍 Rio de Janeiro · Híbrido" in texto
    assert "🏷️ Fonte: Adzuna" in texto
    assert "Publicada em 25/08/2026" in texto


def test_modalidade_nao_informada_aparece_explicitamente():
    texto = formatar_mensagem([resultado(85)], DATA_DE_TESTE)

    assert "📍 Rio de Janeiro · Modalidade não informada" in texto


def test_escapa_localizacao_e_fonte_dos_metadados():
    oportunidade = vaga().model_copy(
        update={"localizacao": "Rio <Centro> & região", "fonte": "portal_exemplo"}
    )
    texto = formatar_mensagem(
        [resultado(85).model_copy(update={"vaga": oportunidade})], DATA_DE_TESTE
    )

    assert "Rio &lt;Centro&gt; &amp; região" in texto
    assert "Fonte: Portal Exemplo" in texto
    assert "Rio <Centro>" not in texto


def test_linha_de_pontos_some_quando_a_lista_esta_vazia():
    so_contra = formatar_mensagem(
        [resultado(10, a_favor=[], contra=["Fora da área"])], DATA_DE_TESTE
    )
    so_a_favor = formatar_mensagem([resultado(95, a_favor=["Python"], contra=[])], DATA_DE_TESTE)

    assert "✅" not in so_contra
    assert "❌ Fora da área" in so_contra
    assert "✅ Python" in so_a_favor
    assert "❌" not in so_a_favor


def test_exibe_no_maximo_tres_pontos_de_cada_tipo():
    texto = formatar_mensagem(
        [
            resultado(
                80,
                a_favor=["Python", "SQL", "Git", "Docker"],
                contra=["Java", "AWS", "Presencial", "Inglês"],
            )
        ],
        DATA_DE_TESTE,
    )

    assert "✅ Python · SQL · Git" in texto
    assert "❌ Java · AWS · Presencial" in texto
    assert "Docker" not in texto
    assert "Inglês" not in texto


def test_alerta_aparece_somente_quando_existe():
    com_alerta = formatar_mensagem([resultado(30, alerta="Exige pleno")], DATA_DE_TESTE)
    sem_alerta = formatar_mensagem([resultado(30)], DATA_DE_TESTE)

    assert "⚠️ Exige pleno" in com_alerta
    assert "⚠️" not in sem_alerta


def test_aviso_objetivo_aparece_separado_dos_pontos_contra():
    texto = formatar_mensagem(
        [
            resultado(
                85,
                contra=["SQL não informado"],
                avisos=["Nota limitada a 30: modalidade incompatível"],
            )
        ],
        DATA_DE_TESTE,
    )

    assert "❌ SQL não informado" in texto
    assert "⚠️ Nota limitada a 30: modalidade incompatível" in texto
    assert "❌ Nota limitada" not in texto


def test_escapa_caracteres_html_dos_dados_da_vaga_e_dos_pontos():
    texto = formatar_mensagem(
        [resultado(50, titulo="Dev <Júnior> & Estágio", contra=["C++ & <Go>"])], DATA_DE_TESTE
    )

    assert "Dev &lt;Júnior&gt; &amp; Estágio" in texto
    assert "C++ &amp; &lt;Go&gt;" in texto
    assert "<Júnior>" not in texto


def test_vagas_sao_separadas_por_linha_divisoria():
    texto = formatar_mensagem([resultado(50, numero=1), resultado(40, numero=2)], DATA_DE_TESTE)

    assert texto.count("───────────────") == 1
    assert texto.index("1. ") < texto.index("───────────────") < texto.index("2. ")


def test_mensagem_curta_nao_e_dividida():
    texto = formatar_mensagem([resultado(50)], DATA_DE_TESTE)

    assert dividir_em_mensagens(texto) == [texto]


def test_mensagem_longa_e_dividida_sem_quebrar_vagas():
    resultados = [
        resultado(50, titulo="Estágio " + "x" * 400, numero=numero) for numero in range(20)
    ]
    texto = formatar_mensagem(resultados, DATA_DE_TESTE)

    partes = dividir_em_mensagens(texto)

    assert len(partes) > 1
    assert all(len(parte) <= LIMITE_DE_CARACTERES_DO_TELEGRAM for parte in partes)
    assert all(parte.count("<b>") == parte.count("</b>") for parte in partes)
    assert "\n\n───────────────\n\n".join(partes) == texto
