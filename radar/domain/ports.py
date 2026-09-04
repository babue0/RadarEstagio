from typing import Protocol

from radar.domain.models import ExtracaoDaVaga, Recomendacao, ResultadoMatch, Usuario, Vaga


class ColetorDeVagas(Protocol):
    def coletar(self) -> list[Vaga]: ...


class ExtratorDeVagas(Protocol):
    def extrair(self, vagas: list[Vaga]) -> list[ExtracaoDaVaga]: ...


class Notificador(Protocol):
    def enviar(self, chat_id: str, texto: str) -> None: ...


class RepositorioDeUsuarios(Protocol):
    def listar_ativos(self) -> list[Usuario]: ...


class RepositorioDeAvaliacoes(Protocol):
    def avaliacoes_existentes(
        self, usuario: Usuario, vagas: list[Vaga]
    ) -> list[ResultadoMatch]: ...

    def ids_ja_enviadas(self, usuario: Usuario) -> set[tuple[str, str]]: ...

    def extracoes_existentes(self, vagas: list[Vaga]) -> dict[str, ExtracaoDaVaga]: ...

    def guardar_extracoes(
        self, extracoes: list[tuple[Vaga, ExtracaoDaVaga]], modelo: str
    ) -> None: ...

    def guardar_avaliacoes(
        self, usuario: Usuario, avaliadas: list[ResultadoMatch], modelo: str
    ) -> None: ...

    def registrar_envios(self, usuario: Usuario, enviadas: list[Recomendacao]) -> None: ...

    def registrar_falha_de_envio(self, usuario: Usuario) -> int: ...

    def registrar_aviso_de_silencio(self, usuario: Usuario) -> None: ...

    def pausar(self, usuario: Usuario) -> None: ...


class Repositorio(RepositorioDeUsuarios, RepositorioDeAvaliacoes, Protocol): ...
