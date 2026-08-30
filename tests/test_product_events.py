import re
from pathlib import Path

RAIZ = Path(__file__).parent.parent
MIGRATION = RAIZ / "supabase/migrations/0005_eventos_produto.sql"
EVENTOS = {
    "landing_visualizada",
    "cta_cadastro_aberto",
    "etapa_perfil_concluida",
    "etapa_habilidades_concluida",
    "etapa_preferencias_concluida",
    "conta_criada",
    "email_confirmado",
    "perfil_salvo",
    "telegram_aberto",
    "telegram_vinculado",
    "primeira_recomendacao_enviada",
    "vaga_aberta",
    "vaga_util",
    "vaga_irrelevante",
    "candidatura_iniciada",
    "entregas_pausadas",
}


def test_migration_declara_todos_os_eventos_minimos():
    sql = MIGRATION.read_text()
    declaracao = sql.split(");", maxsplit=1)[0]

    assert set(re.findall(r"'([a-z_]+)'", declaracao)) == EVENTOS


def test_eventos_guardam_identidade_origem_contexto_e_instante():
    sql = MIGRATION.read_text()

    assert "create table public.eventos_produto" in sql
    assert "sessao_id      uuid" in sql
    assert "user_id        uuid references auth.users" in sql
    assert "perfil_id      uuid references public.perfis" in sql
    assert "vaga_id        bigint references public.vagas" in sql
    assert "propriedades  jsonb" in sql
    assert "ocorrido_em    timestamptz" in sql


def test_frontend_so_pode_inserir_eventos_web_permitidos():
    sql = MIGRATION.read_text()

    assert "alter table public.eventos_produto enable row level security" in sql
    assert 'create policy "visitante registra eventos publicos"' in sql
    assert 'create policy "usuario registra eventos do proprio funil"' in sql
    assert "user_id = auth.uid()" in sql
    assert "octet_length(propriedades::text) <= 4096" in sql


def test_banco_registra_marcos_autoritativos_por_gatilhos():
    sql = MIGRATION.read_text()

    assert "after insert or update of email_confirmed_at on auth.users" in sql
    assert "after insert or update of telegram_chat_id, ativado_em, ativo on public.perfis" in sql
    for evento in {
        "conta_criada",
        "email_confirmado",
        "perfil_salvo",
        "telegram_vinculado",
        "primeira_recomendacao_enviada",
        "entregas_pausadas",
    }:
        assert f"'{evento}', 'banco'" in sql


def test_frontend_instrumenta_a_jornada_que_ja_existe():
    javascript = (RAIZ / "web/assets/app.js").read_text()

    assert 'const eventSessionKey = "radar-sessao-eventos"' in javascript
    assert '.from("eventos_produto").insert' in javascript
    for evento in {
        "landing_visualizada",
        "cta_cadastro_aberto",
        "etapa_perfil_concluida",
        "etapa_habilidades_concluida",
        "etapa_preferencias_concluida",
        "perfil_salvo",
        "telegram_aberto",
    }:
        assert f'registerEvent("{evento}"' in javascript


def test_ctas_identificam_a_posicao_sem_coletar_texto_livre():
    html = (RAIZ / "web/index.html").read_text()

    assert 'data-event-origin="cabecalho"' in html
    assert 'data-event-origin="hero"' in html
    assert 'data-event-origin="como_funciona"' in html
    assert 'data-event-origin="cta_final"' in html
