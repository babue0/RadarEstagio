from typing import Protocol

from radar.domain.models import Perfil, ResultadoMatch, Usuario, Vaga


class ColetorDeVagas(Protocol):
    def coletar(self) -> list[Vaga]: ...


class AvaliadorDeVagas(Protocol):
    def avaliar(self, vagas: list[Vaga], perfil: Perfil) -> list[ResultadoMatch]: ...


class Notificador(Protocol):
    def enviar(self, chat_id: str, texto: str) -> None: ...


class RepositorioDeUsuarios(Protocol):
    def listar_ativos(self) -> list[Usuario]: ...


class RepositorioDeAvaliacoes(Protocol):
    def avaliacoes_existentes(
        self, usuario: Usuario, vagas: list[Vaga]
    ) -> list[ResultadoMatch]: ...

    def ids_ja_enviadas(self, usuario: Usuario) -> set[tuple[str, str]]: ...

    def guardar_avaliacoes(
        self, usuario: Usuario, avaliadas: list[ResultadoMatch], modelo: str
    ) -> None: ...

    def registrar_envios(self, usuario: Usuario, enviadas: list[ResultadoMatch]) -> None: ...

    def registrar_falha_de_envio(self, usuario: Usuario) -> int: ...

    def pausar(self, usuario: Usuario) -> None: ...


class Repositorio(RepositorioDeUsuarios, RepositorioDeAvaliacoes, Protocol): ...
