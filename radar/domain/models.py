from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Modalidade(StrEnum):
    REMOTO = "remoto"
    PRESENCIAL = "presencial"
    HIBRIDO = "hibrido"
    INDIFERENTE = "indiferente"


class Vaga(BaseModel):
    id_externo: str
    fonte: str
    titulo: str
    empresa: str
    localizacao: str
    descricao: str
    url: str
    publicada_em: datetime


class Perfil(BaseModel):
    curso: str
    periodo: int = Field(ge=1)
    habilidades: list[str] = Field(min_length=1)
    cidade: str
    modalidade: Modalidade


class ResultadoMatch(BaseModel):
    vaga: Vaga
    nota: int = Field(ge=0, le=100)
    motivo: str
    alerta_pegadinha: str | None = None
