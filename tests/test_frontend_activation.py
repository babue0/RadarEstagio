from pathlib import Path

RAIZ = Path(__file__).parent.parent


def test_formulario_carrega_supabase_antes_da_aplicacao():
    html = (RAIZ / "web/index.html").read_text()

    assert html.index("@supabase/supabase-js@2") < html.index("config.js")
    assert html.index("config.js") < html.index("assets/app.js")
    assert 'name="senha"' in html
    assert 'id="telegram-link"' in html


def test_cadastro_persiste_perfil_e_monta_vinculo():
    javascript = (RAIZ / "web/assets/app.js").read_text()

    assert '.from("perfis")' in javascript
    assert ".insert({ user_id: userId, ...profile })" in javascript
    assert "signUp" in javascript
    assert "signInWithPassword" in javascript
    assert "?start=${token}" in javascript
    assert 'localStorage.setItem("radar-perfil"' not in javascript


def test_migration_reserva_campos_de_vinculo_ao_webhook():
    migration = (RAIZ / "supabase/migrations/0002_permissoes_frontend.sql").read_text()

    assert "grant insert (user_id, curso, periodo, habilidades, cidade, modalidade)" in migration
    assert "telegram_chat_id" not in migration
    assert "token_vinculo" not in migration
