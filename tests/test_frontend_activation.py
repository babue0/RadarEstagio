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


def test_envio_final_valida_todos_os_campos_da_etapa_3():
    javascript = (RAIZ / "web/assets/app.js").read_text()
    html = (RAIZ / "web/index.html").read_text()

    assert "if (!validateStep(3)) return;" in javascript
    assert 'name="cidade" required minlength="2" maxlength="120"' in html
    assert 'name="modalidade" value="remoto" required' in html
    assert 'name="email" type="email"' in html
    assert 'name="senha" type="password" autocomplete="new-password" minlength="8"' in html


def test_falha_ao_salvar_perfil_mantem_recuperacao_e_mensagem_humana():
    javascript = (RAIZ / "web/assets/app.js").read_text()

    assert "function humanizeError(error" in javascript
    assert "profilePending" in javascript
    assert "Seus dados continuam salvos neste navegador" in javascript
    assert "setFormMessage(error.message)" not in javascript
    assert "humanizeError(error, { profilePending: true })" in javascript


def test_validacao_do_cadastro_orienta_como_corrigir_cada_campo_invalido():
    javascript = (RAIZ / "web/assets/app.js").read_text()

    assert "Informe uma cidade válida para continuar." in javascript
    assert "Escolha uma modalidade para continuar." in javascript
    assert "Digite um e-mail válido para continuar." in javascript
    assert "Use uma senha com pelo menos 8 caracteres para continuar." in javascript
    assert "const modalidadesAceitas = new Set" in javascript


def test_migration_reserva_campos_de_vinculo_ao_webhook():
    migration = (RAIZ / "supabase/migrations/0002_permissoes_frontend.sql").read_text()

    assert "grant insert (user_id, curso, periodo, habilidades, cidade, modalidade)" in migration
    assert "telegram_chat_id" not in migration
    assert "token_vinculo" not in migration


def test_dono_desvincula_o_telegram_e_o_token_e_rotacionado():
    sql = (RAIZ / "supabase/migrations/0013_controle_do_proprio_perfil.sql").read_text()

    assert "create function public.desvincular_meu_telegram()" in sql
    assert "telegram_chat_id = null" in sql
    assert "token_vinculo = gen_random_uuid()" in sql
    assert "where user_id = auth.uid()" in sql


def test_exclusao_da_conta_exige_sessao_e_apaga_o_usuario_de_auth():
    sql = (RAIZ / "supabase/migrations/0013_controle_do_proprio_perfil.sql").read_text()

    assert "create function public.excluir_minha_conta()" in sql
    assert "dono uuid := auth.uid()" in sql
    assert "raise exception 'sem sessão'" in sql
    assert "delete from auth.users where id = dono" in sql


def test_controle_do_perfil_e_fechado_a_visitante_anonimo():
    sql = (RAIZ / "supabase/migrations/0013_controle_do_proprio_perfil.sql").read_text()

    for funcao in ("desvincular_meu_telegram", "excluir_minha_conta"):
        assert f"revoke all on function public.{funcao}() from public, anon" in sql
        assert f"grant execute on function public.{funcao}() to authenticated" in sql
        assert "security definer" in sql
        assert "set search_path = ''" in sql
