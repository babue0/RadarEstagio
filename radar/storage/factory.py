from collections.abc import Iterator
from contextlib import contextmanager
from uuid import UUID

import psycopg

from radar.domain.models import Usuario
from radar.domain.perfil_fixo import perfil_do_mvp
from radar.domain.ports import Repositorio
from radar.settings import Settings
from radar.storage.errors import ErroDeArmazenamento
from radar.storage.memoria import RepositorioEmMemoria
from radar.storage.postgres import RepositorioPostgres

ID_DO_USUARIO_FIXO = UUID("00000000-0000-0000-0000-000000000001")
TIMEOUT_DE_CONEXAO_EM_SEGUNDOS = 10


@contextmanager
def abrir_repositorio(settings: Settings) -> Iterator[Repositorio]:
    if not settings.usa_banco():
        with abrir_repositorio_em_memoria(settings) as repositorio:
            yield repositorio
        return
    try:
        conexao = psycopg.connect(
            settings.database_url, connect_timeout=TIMEOUT_DE_CONEXAO_EM_SEGUNDOS
        )
    except psycopg.Error as erro:
        raise ErroDeArmazenamento(
            f"Não foi possível conectar ao banco ({type(erro).__name__})"
        ) from erro
    with conexao:
        yield RepositorioPostgres(conexao)


@contextmanager
def abrir_repositorio_em_memoria(settings: Settings) -> Iterator[Repositorio]:
    yield RepositorioEmMemoria([usuario_fixo(settings)])


def usuario_fixo(settings: Settings) -> Usuario:
    return Usuario(id=ID_DO_USUARIO_FIXO, perfil=perfil_do_mvp(), chat_id=settings.telegram_chat_id)
