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


def test_funil_monta_o_perfil_antes_de_pedir_a_conta():
    html = (RAIZ / "web/index.html").read_text()

    assert html.count('class="form-step') == 3
    assert html.index('name="curso"') < html.index('name="email"')
    assert html.index('name="habilidades"') < html.index('name="email"')
    assert 'id="cursos-sugeridos"' in html
    assert 'data-skill="Python"' in html


def test_habilidades_sugeridas_e_livres_usam_o_mesmo_campo_do_perfil():
    javascript = (RAIZ / "web/assets/app.js").read_text()

    assert "const selectedSkills = new Set()" in javascript
    assert 'form.elements.habilidades.value = [...selectedSkills].join(",")' in javascript
    assert "Escolha ou digite pelo menos uma habilidade." in javascript
    assert "const totalSteps = 3" in javascript


def test_migration_reserva_campos_de_vinculo_ao_webhook():
    migration = (RAIZ / "supabase/migrations/0002_permissoes_frontend.sql").read_text()

    assert "grant insert (user_id, curso, periodo, habilidades, cidade, modalidade)" in migration
    assert "telegram_chat_id" not in migration
    assert "token_vinculo" not in migration
