import os
from datetime import UTC, datetime
from uuid import uuid4

import psycopg
import pytest

from radar.domain.models import (
    AreaDeInteresse,
    ExtracaoDaVaga,
    Modalidade,
    NivelCompatibilidade,
    Perfil,
    Recomendacao,
    ResultadoMatch,
    Usuario,
    Vaga,
)
from radar.storage.postgres import RepositorioPostgres

DATABASE_URL_TESTE = os.environ.get("DATABASE_URL_TESTE", "")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL_TESTE, reason="defina DATABASE_URL_TESTE para testar contra um Postgres real"
)


@pytest.fixture
def conexao():
    with psycopg.connect(DATABASE_URL_TESTE) as conexao, conexao.transaction(force_rollback=True):
        yield conexao


@pytest.fixture
def usuario(conexao: psycopg.Connection) -> Usuario:
    user_id = uuid4()
    conexao.execute(
        "insert into auth.users (id, instance_id, aud, role, email) "
        "values (%s, '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated', %s)",
        (user_id, f"{user_id}@teste.local"),
    )
    perfil_id = conexao.execute(
        "insert into perfis (user_id, curso, periodo, habilidades, cidade, modalidade, "
        "telegram_chat_id, areas_de_interesse) values (%s, 'Engenharia', 4, '{Python}', "
        "'Rio de Janeiro, RJ', 'remoto', %s, '{desenvolvimento_web}') returning id",
        (user_id, str(uuid4().int)[:9]),
    ).fetchone()[0]
    return RepositorioPostgres(conexao).listar_ativos()[-1].model_copy(update={"id": perfil_id})


def vaga(numero: int, fonte: str = "adzuna") -> Vaga:
    return Vaga(
        id_externo=f"teste-{numero}",
        fonte=fonte,
        titulo=f"Estágio {numero}",
        empresa="Empresa",
        localizacao="Rio de Janeiro",
        descricao="descrição",
        url=f"https://exemplo.com/{numero}",
        publicada_em=datetime(2026, 8, 25, tzinfo=UTC),
        modalidade=Modalidade.REMOTO,
    )


def test_lista_apenas_perfis_ativos_com_chat_id(conexao: psycopg.Connection, usuario: Usuario):
    usuarios = RepositorioPostgres(conexao).listar_ativos()

    assert usuario.id in {item.id for item in usuarios}
    assert all(item.chat_id for item in usuarios)
    assert isinstance(usuarios[0].perfil, Perfil)
    assert usuario.perfil.areas_de_interesse == [AreaDeInteresse.DESENVOLVIMENTO_WEB]


def test_registra_e_recupera_avaliacoes_e_envios(conexao: psycopg.Connection, usuario: Usuario):
    repositorio = RepositorioPostgres(conexao)
    avaliadas = [
        ResultadoMatch(
            vaga=vaga(1),
            nota=80,
            requisitos_atendidos=["Python"],
            requisitos_nao_atendidos=["C#"],
            requisitos_tecnicos_analisados=True,
            pontos_a_favor=["Curso compatível"],
        )
    ]
    enviadas = [Recomendacao(resultado=resultado) for resultado in avaliadas]

    repositorio.guardar_avaliacoes(usuario, avaliadas, "modelo-teste")
    repositorio.registrar_envios(usuario, enviadas)

    existentes = repositorio.avaliacoes_existentes(usuario, [vaga(1), vaga(2)])
    assert [resultado.nota for resultado in existentes] == [80]
    assert existentes[0].requisitos_atendidos == ["Python"]
    assert existentes[0].requisitos_nao_atendidos == ["C#"]
    assert existentes[0].requisitos_tecnicos_analisados
    assert existentes[0].pontos_a_favor == ["Curso compatível"]
    assert repositorio.ids_ja_enviadas(usuario) == {("adzuna", "teste-1")}
    assert conexao.execute("select ativado_em from perfis where id = %s", (usuario.id,)).fetchone()[
        0
    ]
    assert (
        conexao.execute(
            "select count(*) from eventos_produto "
            "where perfil_id = %s and nome = 'primeira_recomendacao_enviada'",
            (usuario.id,),
        ).fetchone()[0]
        == 1
    )


def test_registrar_duas_vezes_nao_duplica(conexao: psycopg.Connection, usuario: Usuario):
    repositorio = RepositorioPostgres(conexao)
    resultado = ResultadoMatch(vaga=vaga(1), nota=80)

    repositorio.guardar_avaliacoes(usuario, [resultado], "modelo")
    repositorio.registrar_envios(usuario, [Recomendacao(resultado=resultado)])
    primeira_ativacao = conexao.execute(
        "select ativado_em from perfis where id = %s", (usuario.id,)
    ).fetchone()[0]
    repositorio.guardar_avaliacoes(usuario, [resultado], "modelo")
    repositorio.registrar_envios(usuario, [Recomendacao(resultado=resultado)])

    assert len(repositorio.avaliacoes_existentes(usuario, [vaga(1)])) == 1
    assert (
        conexao.execute("select count(*) from vagas where id_externo = 'teste-1'").fetchone()[0]
        == 1
    )
    assert (
        conexao.execute("select ativado_em from perfis where id = %s", (usuario.id,)).fetchone()[0]
        == primeira_ativacao
    )
    assert (
        conexao.execute(
            "select count(*) from eventos_produto "
            "where perfil_id = %s and nome = 'primeira_recomendacao_enviada'",
            (usuario.id,),
        ).fetchone()[0]
        == 1
    )


def test_nao_ativa_sem_vaga_enviada(conexao: psycopg.Connection, usuario: Usuario):
    resultado = ResultadoMatch(vaga=vaga(1), nota=40)

    RepositorioPostgres(conexao).guardar_avaliacoes(usuario, [resultado], "modelo")

    assert (
        conexao.execute("select ativado_em from perfis where id = %s", (usuario.id,)).fetchone()[0]
        is None
    )


def test_falhas_seguidas_sao_contadas_e_zeradas_pelo_envio(
    conexao: psycopg.Connection, usuario: Usuario
):
    repositorio = RepositorioPostgres(conexao)

    assert repositorio.registrar_falha_de_envio(usuario) == 1
    assert repositorio.registrar_falha_de_envio(usuario) == 2

    repositorio.registrar_envios(
        usuario, [Recomendacao(resultado=ResultadoMatch(vaga=vaga(1), nota=80))]
    )

    assert (
        conexao.execute(
            "select falhas_de_envio from perfis where id = %s", (usuario.id,)
        ).fetchone()[0]
        == 0
    )


def test_pausar_desativa_o_perfil_e_registra_o_evento(
    conexao: psycopg.Connection, usuario: Usuario
):
    RepositorioPostgres(conexao).pausar(usuario)

    assert (
        conexao.execute("select ativo from perfis where id = %s", (usuario.id,)).fetchone()[0]
        is False
    )
    assert (
        conexao.execute(
            "select count(*) from eventos_produto "
            "where perfil_id = %s and nome = 'entregas_pausadas'",
            (usuario.id,),
        ).fetchone()[0]
        == 1
    )


def test_usuario_ativo_traz_desde_quando_esta_sem_recomendacao(
    conexao: psycopg.Connection, usuario: Usuario
):
    repositorio = RepositorioPostgres(conexao)
    criado_em = conexao.execute(
        "select criado_em from perfis where id = %s", (usuario.id,)
    ).fetchone()[0]

    antes = next(item for item in repositorio.listar_ativos() if item.id == usuario.id)
    assert antes.sem_recomendacao_desde == criado_em
    assert antes.silencio_avisado_em is None

    repositorio.registrar_envios(
        usuario, [Recomendacao(resultado=ResultadoMatch(vaga=vaga(1), nota=80))]
    )
    repositorio.registrar_aviso_de_silencio(usuario)

    depois = next(item for item in repositorio.listar_ativos() if item.id == usuario.id)
    assert depois.sem_recomendacao_desde > criado_em
    assert depois.silencio_avisado_em is not None


def test_extracao_e_guardada_na_vaga_e_reaproveitada(conexao: psycopg.Connection):
    repositorio = RepositorioPostgres(conexao)
    extracao = ExtracaoDaVaga(
        id_vaga="teste-1",
        area_de_tecnologia=NivelCompatibilidade.COMPATIVEL,
        cursos_aceitos=["Ciência da Computação"],
        habilidades_obrigatorias=["Python"],
        periodo_minimo=3,
    )

    assert repositorio.extracoes_existentes([vaga(1)]) == {}

    repositorio.guardar_extracoes([(vaga(1), extracao)], "modelo-teste")

    guardadas = repositorio.extracoes_existentes([vaga(1), vaga(2)])
    assert list(guardadas) == ["teste-1"]
    assert guardadas["teste-1"] == extracao
    assert (
        conexao.execute(
            "select modelo_extracao from vagas where id_externo = 'teste-1'"
        ).fetchone()[0]
        == "modelo-teste"
    )


def test_envio_guarda_o_token_do_link_rastreavel(conexao: psycopg.Connection, usuario: Usuario):
    recomendacao = Recomendacao(resultado=ResultadoMatch(vaga=vaga(1), nota=80))

    RepositorioPostgres(conexao).registrar_envios(usuario, [recomendacao])

    assert (
        conexao.execute("select token from envios where perfil_id = %s", (usuario.id,)).fetchone()[
            0
        ]
        == recomendacao.token
    )
