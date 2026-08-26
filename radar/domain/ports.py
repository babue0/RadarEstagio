from typing import Protocol

from radar.domain.models import Perfil, ResultadoMatch, Vaga


class ColetorDeVagas(Protocol):
    def coletar(self) -> list[Vaga]: ...


class AvaliadorDeVagas(Protocol):
    def avaliar(self, vaga: Vaga, perfil: Perfil) -> ResultadoMatch: ...


class Notificador(Protocol):
    def enviar(self, texto: str) -> None: ...
