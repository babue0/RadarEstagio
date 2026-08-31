import logging
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from radar.domain.models import Modalidade, Perfil, ResultadoMatch, Usuario, Vaga
from radar.storage.errors import ErroDeArmazenamento

logger = logging.getLogger(__name__)

SQL_USUARIOS_ATIVOS = """
    select id, curso, periodo, habilidades, cidade, modalidade, telegram_chat_id
    from perfis
    where ativo and telegram_chat_id is not null
    order by criado_em
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

    def registrar(
        self,
        usuario: Usuario,
        avaliadas: list[ResultadoMatch],
        enviadas: list[ResultadoMatch],
        modelo: str,
    ) -> None:
        ativado_agora = False
        try:
            with self._conexao.transaction(), self._conexao.cursor() as cursor:
                ids_das_vagas = {
                    chave(resultado.vaga): guardar_vaga(cursor, resultado.vaga)
                    for resultado in avaliadas + enviadas
                }
                for resultado in avaliadas:
                    guardar_avaliacao(
                        cursor, usuario.id, ids_das_vagas[chave(resultado.vaga)], resultado, modelo
                    )
                for resultado in enviadas:
                    guardar_envio(cursor, usuario.id, ids_das_vagas[chave(resultado.vaga)])
                if enviadas:
                    ativado_agora = registrar_ativacao(cursor, usuario.id)
        except psycopg.Error as erro:
            raise ErroDeArmazenamento(
                f"Falha ao gravar avaliações e envios: {descrever(erro)}"
            ) from erro
        if ativado_agora:
            logger.info("Perfil %s ativado pela primeira entrega relevante", usuario.id)


def chave(vaga: Vaga) -> tuple[str, str]:
    return (vaga.fonte, vaga.id_externo)


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
        ),
        chat_id=linha["telegram_chat_id"],
    )


def descrever(erro: psycopg.Error) -> str:
    return type(erro).__name__
