from datetime import UTC, datetime
from uuid import uuid4

from radar.domain.models import ResultadoMatch, Usuario, Vaga
from radar.domain.perfil_fixo import perfil_do_mvp
from radar.storage.memoria import RepositorioEmMemoria


def usuario_exemplo() -> Usuario:
    return Usuario(id=uuid4(), perfil=perfil_do_mvp(), chat_id="123")


def vaga_exemplo() -> Vaga:
    return Vaga(
        id_externo="1",
        fonte="adzuna",
        titulo="Estágio Python",
        empresa="Empresa",
        localizacao="Rio de Janeiro",
        descricao="descrição",
        url="https://exemplo.com/1",
        publicada_em=datetime(2026, 8, 25, tzinfo=UTC),
    )


def test_lista_os_usuarios_recebidos():
    usuario = usuario_exemplo()

    assert RepositorioEmMemoria([usuario]).listar_ativos() == [usuario]


def test_nao_guarda_nada_entre_chamadas():
    usuario = usuario_exemplo()
    repositorio = RepositorioEmMemoria([usuario])
    resultado = ResultadoMatch(vaga=vaga_exemplo(), nota=80)

    repositorio.registrar(usuario, [resultado], [resultado], "modelo")

    assert repositorio.avaliacoes_existentes(usuario, [vaga_exemplo()]) == []
    assert repositorio.ids_ja_enviadas(usuario) == set()
