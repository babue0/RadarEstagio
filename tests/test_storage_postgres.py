import os
from datetime import UTC, datetime
from uuid import uuid4

import psycopg
import pytest

from radar.domain.models import Modalidade, Perfil, ResultadoMatch, Usuario, Vaga
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
        "telegram_chat_id) values (%s, 'Engenharia', 4, '{Python}', 'Rio de Janeiro, RJ', "
        "'remoto', %s) returning id",
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


def test_registra_e_recupera_avaliacoes_e_envios(conexao: psycopg.Connection, usuario: Usuario):
    repositorio = RepositorioPostgres(conexao)
    avaliadas = [ResultadoMatch(vaga=vaga(1), nota=80, pontos_a_favor=["Python"])]
    enviadas = avaliadas

    repositorio.registrar(usuario, avaliadas, enviadas, "modelo-teste")

    existentes = repositorio.avaliacoes_existentes(usuario, [vaga(1), vaga(2)])
    assert [resultado.nota for resultado in existentes] == [80]
    assert existentes[0].pontos_a_favor == ["Python"]
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

    repositorio.registrar(usuario, [resultado], [resultado], "modelo")
    primeira_ativacao = conexao.execute(
        "select ativado_em from perfis where id = %s", (usuario.id,)
    ).fetchone()[0]
    repositorio.registrar(usuario, [resultado], [resultado], "modelo")

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

    RepositorioPostgres(conexao).registrar(usuario, [resultado], [], "modelo")

    assert (
        conexao.execute("select ativado_em from perfis where id = %s", (usuario.id,)).fetchone()[0]
        is None
    )
