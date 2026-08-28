from radar.domain.models import ResultadoMatch, Usuario, Vaga


class RepositorioEmMemoria:
    def __init__(self, usuarios: list[Usuario]) -> None:
        self._usuarios = usuarios

    def listar_ativos(self) -> list[Usuario]:
        return list(self._usuarios)

    def avaliacoes_existentes(self, usuario: Usuario, vagas: list[Vaga]) -> list[ResultadoMatch]:
        return []

    def ids_ja_enviadas(self, usuario: Usuario) -> set[tuple[str, str]]:
        return set()

    def registrar(
        self,
        usuario: Usuario,
        avaliadas: list[ResultadoMatch],
        enviadas: list[ResultadoMatch],
        modelo: str,
    ) -> None:
        return None
