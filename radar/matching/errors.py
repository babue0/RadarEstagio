class ErroDeAvaliacao(Exception):
    pass


class CotaDeAvaliacaoExcedida(ErroDeAvaliacao):
    def __init__(self, mensagem: str, aguardar_segundos: float | None = None) -> None:
        super().__init__(mensagem)
        self.aguardar_segundos = aguardar_segundos
