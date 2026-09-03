from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class Modalidade(StrEnum):
    REMOTO = "remoto"
    PRESENCIAL = "presencial"
    HIBRIDO = "hibrido"
    INDIFERENTE = "indiferente"


class AreaDeInteresse(StrEnum):
    DESENVOLVIMENTO_WEB = "desenvolvimento_web"
    DESENVOLVIMENTO_MOBILE = "desenvolvimento_mobile"
    DADOS_IA = "dados_ia"
    INFRAESTRUTURA_REDES = "infraestrutura_redes"
    SEGURANCA = "seguranca"
    SUPORTE_TECNICO = "suporte_tecnico"
    QA_TESTES = "qa_testes"


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
    descricao_completa: bool = True


class Perfil(BaseModel):
    curso: str
    periodo: int = Field(ge=1)
    habilidades: list[str] = Field(min_length=1)
    cidade: str
    modalidade: Modalidade
    areas_de_interesse: list[AreaDeInteresse] = Field(default_factory=list)

    def nome_da_cidade(self) -> str:
        return self.cidade.split(",")[0].strip()


class Usuario(BaseModel):
    id: UUID
    perfil: Perfil
    chat_id: str = Field(min_length=1)
    sem_recomendacao_desde: datetime | None = None
    silencio_avisado_em: datetime | None = None


class ResultadoMatch(BaseModel):
    vaga: Vaga
    nota: int = Field(ge=0, le=100)
    requisitos_atendidos: list[str] = Field(default_factory=list)
    requisitos_nao_atendidos: list[str] = Field(default_factory=list)
    requisitos_tecnicos_analisados: bool = False
    pontos_a_favor: list[str] = Field(default_factory=list)
    pontos_contra: list[str] = Field(default_factory=list)
    avisos_objetivos: list[str] = Field(default_factory=list)
    alerta_pegadinha: str | None = None
