import logging
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from radar.domain.models import (
    AreaDeInteresse,
    ExtracaoDaVaga,
    Modalidade,
    Perfil,
    ResultadoMatch,
    Usuario,
    Vaga,
)
from radar.storage.errors import ErroDeArmazenamento

logger = logging.getLogger(__name__)

SQL_USUARIOS_ATIVOS = """
    select p.id, p.curso, p.periodo, p.habilidades, p.cidade, p.modalidade, p.telegram_chat_id,
           coalesce(p.areas_de_interesse, '{}'::text[]) as areas_de_interesse,
           coalesce(
             (select max(e.enviada_em) from envios e where e.perfil_id = p.id),
             p.criado_em
           ) as sem_recomendacao_desde,
           p.silencio_avisado_em
    from perfis p
    where p.ativo and p.telegram_chat_id is not null
    order by p.criado_em
"""

SQL_PERFIS_SEM_VINCULO = "select count(*) from perfis where ativo and telegram_chat_id is null"

SQL_AVALIACOES_EXISTENTES = """
    select v.fonte, v.id_externo, a.nota,
           a.requisitos_atendidos, a.requisitos_nao_atendidos,
           a.requisitos_tecnicos_analisados,
           a.pontos_a_favor, a.pontos_contra, a.alerta_pegadinha
    from avaliacoes a
    join vagas v on v.id = a.vaga_id
    where a.perfil_id = %(perfil_id)s
      and (v.fonte, v.id_externo) in (
        select * from unnest(%(fontes)s::text[], %(ids_externos)s::text[])
      )
"""

SQL_EXTRACOES_EXISTENTES = """
    select id_externo, extracao
    from vagas
    where extracao is not null
      and (fonte, id_externo) in (
        select * from unnest(%(fontes)s::text[], %(ids_externos)s::text[])
      )
"""

SQL_GUARDAR_EXTRACAO = """
    update vagas
    set extracao = %(extracao)s, extraida_em = now(), modelo_extracao = %(modelo)s
    where id = %(vaga_id)s
"""

SQL_IDS_ENVIADOS = """
    select v.fonte, v.id_externo
    from envios e
    join vagas v on v.id = e.vaga_id
    where e.perfil_id = %(perfil_id)s
"""

SQL_GUARDAR_VAGA = """
    insert into vagas
      (fonte, id_externo, titulo, empresa, localizacao, descricao, url, publicada_em, modalidade)
    values
      (%(fonte)s, %(id_externo)s, %(titulo)s, %(empresa)s, %(localizacao)s, %(descricao)s,
       %(url)s, %(publicada_em)s, %(modalidade)s)
    on conflict (fonte, id_externo) do update set
      descricao = case
        when length(excluded.descricao) > length(vagas.descricao) then excluded.descricao
        else vagas.descricao
      end,
      modalidade = coalesce(excluded.modalidade, vagas.modalidade)
    returning id
"""

SQL_GUARDAR_AVALIACAO = """
    insert into avaliacoes
      (perfil_id, vaga_id, nota, requisitos_atendidos, requisitos_nao_atendidos,
       requisitos_tecnicos_analisados, pontos_a_favor, pontos_contra, alerta_pegadinha, modelo)
    values
      (%(perfil_id)s, %(vaga_id)s, %(nota)s, %(requisitos_atendidos)s,
       %(requisitos_nao_atendidos)s, %(requisitos_tecnicos_analisados)s,
       %(pontos_a_favor)s, %(pontos_contra)s, %(alerta_pegadinha)s, %(modelo)s)
    on conflict (perfil_id, vaga_id) do nothing
"""

SQL_GUARDAR_ENVIO = """
    insert into envios (perfil_id, vaga_id)
    values (%(perfil_id)s, %(vaga_id)s)
    on conflict (perfil_id, vaga_id) do nothing
"""

SQL_REGISTRAR_ATIVACAO = """
    update perfis
    set ativado_em = now()
    where id = %(perfil_id)s and ativado_em is null
    returning ativado_em
"""

SQL_ZERAR_FALHAS_DE_ENVIO = """
    update perfis
    set falhas_de_envio = 0
    where id = %(perfil_id)s and falhas_de_envio > 0
"""

SQL_CONTAR_FALHA_DE_ENVIO = """
    update perfis
    set falhas_de_envio = falhas_de_envio + 1
    where id = %(perfil_id)s
    returning falhas_de_envio
"""

SQL_PAUSAR = """
    update perfis
    set ativo = false, atualizado_em = now()
    where id = %(perfil_id)s and ativo
"""

SQL_REGISTRAR_AVISO_DE_SILENCIO = """
    update perfis
    set silencio_avisado_em = now()
    where id = %(perfil_id)s
"""


class RepositorioPostgres:
    def __init__(self, conexao: psycopg.Connection) -> None:
        self._conexao = conexao

    def listar_ativos(self) -> list[Usuario]:
        try:
            with self._conexao.cursor(row_factory=dict_row) as cursor:
                linhas = cursor.execute(SQL_USUARIOS_ATIVOS).fetchall()
                sem_vinculo = cursor.execute(SQL_PERFIS_SEM_VINCULO).fetchone()["count"]
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(f"Falha ao ler os perfis: {descrever(erro)}") from erro
        if sem_vinculo:
            logger.info("%d perfis ativos ainda sem Telegram vinculado", sem_vinculo)
        return [converter_em_usuario(linha) for linha in linhas]

    def extracoes_existentes(self, vagas: list[Vaga]) -> dict[str, ExtracaoDaVaga]:
        if not vagas:
            return {}
        parametros = {
            "fontes": [vaga.fonte for vaga in vagas],
            "ids_externos": [vaga.id_externo for vaga in vagas],
        }
        try:
            with self._conexao.cursor(row_factory=dict_row) as cursor:
                linhas = cursor.execute(SQL_EXTRACOES_EXISTENTES, parametros).fetchall()
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(f"Falha ao ler as extrações: {descrever(erro)}") from erro
        return {
            linha["id_externo"]: ExtracaoDaVaga.model_validate(linha["extracao"])
            for linha in linhas
        }

    def guardar_extracoes(self, extracoes: list[tuple[Vaga, ExtracaoDaVaga]], modelo: str) -> None:
        if not extracoes:
            return
        try:
            with self._conexao.transaction(), self._conexao.cursor() as cursor:
                for vaga, extracao in extracoes:
                    vaga_id = guardar_vaga(cursor, vaga)
                    cursor.execute(
                        SQL_GUARDAR_EXTRACAO,
                        {
                            "vaga_id": vaga_id,
                            "extracao": Jsonb(extracao.model_dump(mode="json")),
                            "modelo": modelo,
                        },
                    )
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(f"Falha ao gravar as extrações: {descrever(erro)}") from erro

    def avaliacoes_existentes(self, usuario: Usuario, vagas: list[Vaga]) -> list[ResultadoMatch]:
        if not vagas:
            return []
        vagas_por_chave = {(vaga.fonte, vaga.id_externo): vaga for vaga in vagas}
        parametros = {
            "perfil_id": usuario.id,
            "fontes": [vaga.fonte for vaga in vagas],
            "ids_externos": [vaga.id_externo for vaga in vagas],
        }
        try:
            with self._conexao.cursor(row_factory=dict_row) as cursor:
                linhas = cursor.execute(SQL_AVALIACOES_EXISTENTES, parametros).fetchall()
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(f"Falha ao ler as avaliações: {descrever(erro)}") from erro
        return [
            ResultadoMatch(
                vaga=vagas_por_chave[(linha["fonte"], linha["id_externo"])],
                nota=linha["nota"],
                requisitos_atendidos=linha["requisitos_atendidos"],
                requisitos_nao_atendidos=linha["requisitos_nao_atendidos"],
                requisitos_tecnicos_analisados=linha["requisitos_tecnicos_analisados"],
                pontos_a_favor=linha["pontos_a_favor"],
                pontos_contra=linha["pontos_contra"],
                alerta_pegadinha=linha["alerta_pegadinha"],
            )
            for linha in linhas
        ]

    def ids_ja_enviadas(self, usuario: Usuario) -> set[tuple[str, str]]:
        try:
            with self._conexao.cursor() as cursor:
                linhas = cursor.execute(SQL_IDS_ENVIADOS, {"perfil_id": usuario.id}).fetchall()
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(f"Falha ao ler os envios: {descrever(erro)}") from erro
        return {(fonte, id_externo) for fonte, id_externo in linhas}

    def guardar_avaliacoes(
        self, usuario: Usuario, avaliadas: list[ResultadoMatch], modelo: str
    ) -> None:
        if not avaliadas:
            return
        try:
            with self._conexao.transaction(), self._conexao.cursor() as cursor:
                for resultado in avaliadas:
                    vaga_id = guardar_vaga(cursor, resultado.vaga)
                    guardar_avaliacao(cursor, usuario.id, vaga_id, resultado, modelo)
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(f"Falha ao gravar avaliações: {descrever(erro)}") from erro

    def registrar_envios(self, usuario: Usuario, enviadas: list[ResultadoMatch]) -> None:
        if not enviadas:
            return
        try:
            with self._conexao.transaction(), self._conexao.cursor() as cursor:
                for resultado in enviadas:
                    vaga_id = guardar_vaga(cursor, resultado.vaga)
                    guardar_envio(cursor, usuario.id, vaga_id)
                ativado_agora = registrar_ativacao(cursor, usuario.id)
                cursor.execute(SQL_ZERAR_FALHAS_DE_ENVIO, {"perfil_id": usuario.id})
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(f"Falha ao gravar envios: {descrever(erro)}") from erro
        if ativado_agora:
            logger.info("Perfil %s ativado pela primeira entrega relevante", usuario.id)

    def registrar_falha_de_envio(self, usuario: Usuario) -> int:
        try:
            with self._conexao.transaction(), self._conexao.cursor() as cursor:
                return cursor.execute(
                    SQL_CONTAR_FALHA_DE_ENVIO, {"perfil_id": usuario.id}
                ).fetchone()[0]
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(
                f"Falha ao contar a falha de envio: {descrever(erro)}"
            ) from erro

    def registrar_aviso_de_silencio(self, usuario: Usuario) -> None:
        try:
            with self._conexao.transaction(), self._conexao.cursor() as cursor:
                cursor.execute(SQL_REGISTRAR_AVISO_DE_SILENCIO, {"perfil_id": usuario.id})
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(
                f"Falha ao gravar o aviso de silêncio: {descrever(erro)}"
            ) from erro

    def pausar(self, usuario: Usuario) -> None:
        try:
            with self._conexao.transaction(), self._conexao.cursor() as cursor:
                cursor.execute(SQL_PAUSAR, {"perfil_id": usuario.id})
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(f"Falha ao pausar o perfil: {descrever(erro)}") from erro


def guardar_vaga(cursor: psycopg.Cursor, vaga: Vaga) -> int:
    parametros = vaga.model_dump(mode="json", exclude={"modalidade"})
    parametros["publicada_em"] = vaga.publicada_em
    parametros["modalidade"] = vaga.modalidade.value if vaga.modalidade else None
    return cursor.execute(SQL_GUARDAR_VAGA, parametros).fetchone()[0]


def guardar_avaliacao(
    cursor: psycopg.Cursor, perfil_id: UUID, vaga_id: int, resultado: ResultadoMatch, modelo: str
) -> None:
    cursor.execute(
        SQL_GUARDAR_AVALIACAO,
        {
            "perfil_id": perfil_id,
            "vaga_id": vaga_id,
            "nota": resultado.nota,
            "requisitos_atendidos": resultado.requisitos_atendidos,
            "requisitos_nao_atendidos": resultado.requisitos_nao_atendidos,
            "requisitos_tecnicos_analisados": resultado.requisitos_tecnicos_analisados,
            "pontos_a_favor": resultado.pontos_a_favor,
            "pontos_contra": resultado.pontos_contra,
            "alerta_pegadinha": resultado.alerta_pegadinha,
            "modelo": modelo,
        },
    )


def guardar_envio(cursor: psycopg.Cursor, perfil_id: UUID, vaga_id: int) -> None:
    cursor.execute(SQL_GUARDAR_ENVIO, {"perfil_id": perfil_id, "vaga_id": vaga_id})


def registrar_ativacao(cursor: psycopg.Cursor, perfil_id: UUID) -> bool:
    return cursor.execute(SQL_REGISTRAR_ATIVACAO, {"perfil_id": perfil_id}).fetchone() is not None


def converter_em_usuario(linha: dict) -> Usuario:
    return Usuario(
        id=linha["id"],
        perfil=Perfil(
            curso=linha["curso"],
            periodo=linha["periodo"],
            habilidades=linha["habilidades"],
            cidade=linha["cidade"],
            modalidade=Modalidade(linha["modalidade"]),
            areas_de_interesse=[AreaDeInteresse(area) for area in linha["areas_de_interesse"]],
        ),
        chat_id=linha["telegram_chat_id"],
        sem_recomendacao_desde=linha["sem_recomendacao_desde"],
        silencio_avisado_em=linha["silencio_avisado_em"],
    )


def descrever(erro: psycopg.Error) -> str:
    return type(erro).__name__
