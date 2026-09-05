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
    assert 'rpc("concluir_meu_cadastro"' in javascript
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
    assert "Entre novamente para concluir o perfil" in javascript
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


def test_exclusao_da_conta_exige_sessao_e_so_marca_a_data():
    sql = (RAIZ / "supabase/migrations/0013_controle_do_proprio_perfil.sql").read_text()
    corpo = sql.split("create function public.excluir_minha_conta()")[1].split("$$;")[0]

    assert "dono uuid := auth.uid()" in corpo
    assert "raise exception 'sem sessão'" in corpo
    assert "excluida_em = coalesce(excluida_em, now())" in corpo
    assert "ativo" not in corpo
    assert "delete from auth.users" not in sql


def test_a_entrega_diaria_ignora_quem_pediu_exclusao():
    codigo = (RAIZ / "radar/storage/postgres.py").read_text()

    assert "where p.ativo and p.excluida_em is null" in codigo


def test_a_limpeza_por_sessao_so_alcanca_evento_sem_dono():
    codigo = (RAIZ / "radar/storage/postgres.py").read_text()
    consulta = codigo.split("SQL_APAGAR_EVENTOS_ANONIMOS")[1].split('"""')[1]

    assert "user_id is null" in consulta


def test_exclusao_pode_ser_cancelada_enquanto_o_prazo_nao_venceu():
    sql = (RAIZ / "supabase/migrations/0013_controle_do_proprio_perfil.sql").read_text()

    corpo = sql.split("create function public.cancelar_exclusao_da_minha_conta()")[1]

    assert "excluida_em = null" in corpo
    assert "ativo" not in corpo.split("$$;")[0]
    assert "where user_id = auth.uid() and excluida_em is not null" in corpo


def test_controle_do_perfil_e_fechado_a_visitante_anonimo():
    sql = (RAIZ / "supabase/migrations/0013_controle_do_proprio_perfil.sql").read_text()

    for funcao in (
        "desvincular_meu_telegram",
        "excluir_minha_conta",
        "cancelar_exclusao_da_minha_conta",
    ):
        assert f"revoke all on function public.{funcao}() from public, anon" in sql
        assert f"grant execute on function public.{funcao}() to authenticated" in sql
        assert "security definer" in sql
        assert "set search_path = ''" in sql


def test_perfil_marcado_para_exclusao_nao_aceita_update_do_site():
    sql = (RAIZ / "supabase/migrations/0013_controle_do_proprio_perfil.sql").read_text()

    assert 'drop policy "usuario edita o proprio perfil" on public.perfis' in sql
    assert "using (auth.uid() = user_id and excluida_em is null)" in sql
    assert "with check (auth.uid() = user_id and excluida_em is null)" in sql


def test_cancelar_a_exclusao_leva_de_volta_ao_vinculo_do_telegram():
    js = (RAIZ / "web/assets/app.js").read_text()
    handler = js.split(
        'querySelector("#cancel-deletion").addEventListener'
    )[1].split("});")[0]

    assert "mostrarEstadoDoPerfil(profile)" in handler
    assert "showAccount(profile)" not in handler
