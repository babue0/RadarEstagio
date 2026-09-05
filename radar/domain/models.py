import unicodedata
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

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


class NivelCompatibilidade(StrEnum):
    COMPATIVEL = "compativel"
    PARCIAL = "parcial"
    INCOMPATIVEL = "incompativel"


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


class ExtracaoDaVaga(BaseModel):
    id_vaga: str
    area_de_tecnologia: NivelCompatibilidade
    areas_da_vaga: list[str] = Field(default_factory=list)
    cursos_aceitos: list[str] = Field(default_factory=list)
    aceita_qualquer_curso: bool = False
    periodo_minimo: int | None = None
    experiencia_minima_anos: int | None = None
    experiencia_desejavel: bool = False
    habilidades_obrigatorias: list[str] = Field(default_factory=list)
    habilidades_principais: list[str] = Field(default_factory=list)
    habilidades_desejaveis: list[str] = Field(default_factory=list)
    modalidade: str | None = None
    alerta_pegadinha: str | None = None

    def modalidade_reconhecida(self) -> Modalidade | None:
        if not self.modalidade:
            return None
        sem_acentos = (
            unicodedata.normalize("NFKD", self.modalidade).encode("ascii", "ignore").decode("ascii")
        )
        try:
            return Modalidade(sem_acentos.strip().casefold())
        except ValueError:
            return None


class Perfil(BaseModel):
    curso: str
    periodo: int = Field(ge=1)
    habilidades: list[str] = Field(min_length=1)
    cidade: str
    modalidade: Modalidade
    areas_de_interesse: list[AreaDeInteresse] = Field(default_factory=list)
    areas_recusadas: list[AreaDeInteresse] = Field(default_factory=list)

    def nome_da_cidade(self) -> str:
        return self.cidade.split(",")[0].strip()


class MotivoDeRecusa(StrEnum):
    AREA = "motivo_area"
    EXIGENCIA = "motivo_exigencia"
    LOGISTICA = "motivo_logistica"
    REPETIDA = "motivo_repetida"


class BotaoDeFeedback(BaseModel):
    rotulo: str = Field(min_length=1)
    dados: str = Field(min_length=1, max_length=64)


class PerguntaDeFeedback(BaseModel):
    texto: str = Field(min_length=1)
    linhas_de_botoes: list[list[BotaoDeFeedback]] = Field(min_length=1)


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


class RecusasDoUsuario(BaseModel):
    areas: list[AreaDeInteresse] = Field(default_factory=list)
    vagas_repetidas: list[Vaga] = Field(default_factory=list)


class Recomendacao(BaseModel):
    resultado: ResultadoMatch
    token: UUID = Field(default_factory=uuid4)


class FunilDaCoorte(BaseModel):
    dias: int = Field(ge=1)
    perfis_criados: int
    perfis_vinculados: int
    perfis_ativados: int
    perfis_com_vaga_aberta: int
    perfis_com_vaga_util: int
    perfis_com_candidatura: int
    vagas_enviadas: int
    vagas_abertas: int
    vagas_uteis: int
    vagas_irrelevantes: int
    candidaturas: int
    vagas_extraidas: int
    recusas_por_motivo: dict[str, int] = Field(default_factory=dict)

    def vagas_extraidas_por_ativado(self) -> float | None:
        if not self.perfis_ativados:
            return None
        return self.vagas_extraidas / self.perfis_ativados
