from datetime import datetime
from enum import StrEnum
from uuid import UUID

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
    modalidade: Modalidade | None = None


class Perfil(BaseModel):
    curso: str
    periodo: int = Field(ge=1)
    habilidades: list[str] = Field(min_length=1)
    cidade: str
    modalidade: Modalidade

    def nome_da_cidade(self) -> str:
        return self.cidade.split(",")[0].strip()


class Usuario(BaseModel):
    id: UUID
    perfil: Perfil
    chat_id: str = Field(min_length=1)


class ResultadoMatch(BaseModel):
    vaga: Vaga
    nota: int = Field(ge=0, le=100)
    pontos_a_favor: list[str] = Field(default_factory=list)
    pontos_contra: list[str] = Field(default_factory=list)
    avisos_objetivos: list[str] = Field(default_factory=list)
    alerta_pegadinha: str | None = None
