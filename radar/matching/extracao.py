from pydantic import BaseModel

from radar.domain.models import ExtracaoDaVaga


class ExtracoesDeVagas(BaseModel):
    extracoes: list[ExtracaoDaVaga]
