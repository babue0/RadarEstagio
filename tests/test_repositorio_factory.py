import pytest

from radar.settings import Settings
from radar.storage.errors import ErroDeArmazenamento
from radar.storage.factory import ID_DO_USUARIO_FIXO, abrir_repositorio
from radar.storage.memoria import RepositorioEmMemoria


def settings_de_teste(**sobrescritas: str) -> Settings:
    valores = {
        "adzuna_app_id": "adzuna-id",
        "adzuna_app_key": "adzuna-chave",
        "avaliador": "agy",
        "telegram_bot_token": "telegram-token",
        "telegram_chat_id": "123",
    }
    valores.update(sobrescritas)
    return Settings(_env_file=None, **valores)


def test_sem_database_url_usa_o_perfil_fixo_em_memoria():
    with abrir_repositorio(settings_de_teste()) as repositorio:
        usuarios = repositorio.listar_ativos()

    assert isinstance(repositorio, RepositorioEmMemoria)
    assert len(usuarios) == 1
    assert usuarios[0].id == ID_DO_USUARIO_FIXO
    assert usuarios[0].chat_id == "123"


def test_banco_inacessivel_levanta_erro_de_armazenamento():
    settings = settings_de_teste(database_url="postgresql://radar@127.0.0.1:1/radar")

    with (
        pytest.raises(ErroDeArmazenamento, match="conectar ao banco"),
        abrir_repositorio(settings),
    ):
        pass
