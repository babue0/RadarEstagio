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

    def guardar_avaliacoes(
        self, usuario: Usuario, avaliadas: list[ResultadoMatch], modelo: str
    ) -> None:
        return None

    def registrar_envios(self, usuario: Usuario, enviadas: list[ResultadoMatch]) -> None:
        return None

    def registrar_falha_de_envio(self, usuario: Usuario) -> int:
        return 0

    def registrar_aviso_de_silencio(self, usuario: Usuario) -> None:
        return None

    def pausar(self, usuario: Usuario) -> None:
        return None
