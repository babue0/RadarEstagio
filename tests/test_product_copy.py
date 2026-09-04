from pathlib import Path

RAIZ = Path(__file__).parent.parent


def test_landing_nao_promete_chegada_antecipada_ou_edicao_inexistente():
    html = (RAIZ / "web/index.html").read_text()

    assert "Chegue antes" not in html
    assert "você poderá editar depois" not in html
    assert "Vagas mais claras" in html


def test_landing_e_cadastro_dizem_para_que_servem_os_dados():
    html = (RAIZ / "web/index.html").read_text()

    assert "Usa isso só para comparar vagas com o seu perfil" in html
    assert "Nada é vendido nem compartilhado com terceiros" in html
    assert "servem só para comparar vagas com o seu perfil" in html
    assert "Nada é vendido nem compartilhado." in html


def test_aviso_de_privacidade_aponta_para_o_painel_que_passou_a_existir():
    html = (RAIZ / "web/index.html").read_text()

    assert "fale com a equipe do projeto" not in html
    assert "entre na sua conta pelo botão de cadastro" in html
    assert 'id="delete-account"' in html


def test_aviso_de_privacidade_do_cadastro_aparece_tambem_no_celular():
    css = (RAIZ / "web/assets/styles.css").read_text()

    assert ".privacy-note { display: none; }" not in css


def test_documentacao_reflete_a_fase_atual_e_as_evidencias_recentes():
    plano = (RAIZ / "docs/plano-melhorias-rcd.md").read_text()
    pre_prd = (RAIZ / "docs/pre-prd.md").read_text()
    proposta = (RAIZ / "docs/proposta.md").read_text()

    assert "Fase 2 — MVP de validação com usuários, parcialmente implementada" in plano
    assert "703 vagas únicas e 55 candidatas" in pre_prd
    assert "703 vagas únicas" in pre_prd
    assert "aprende com o feedback" not in proposta


def test_cadastro_rola_no_celular_em_vez_de_cortar_o_botao():
    css = (RAIZ / "web/assets/styles.css").read_text()
    regra_do_celular = css[css.index("@media (max-width: 760px)") :]

    assert "overflow-y: auto" in regra_do_celular.split(".dialog-shell")[0]


def test_painel_da_conta_oferece_editar_pausar_desvincular_e_excluir():
    html = (RAIZ / "web/index.html").read_text()

    for controle in ("edit-profile", "toggle-deliveries", "unlink-telegram", "delete-account"):
        assert f'id="{controle}"' in html


def test_acao_destrutiva_pede_confirmacao_antes():
    javascript = (RAIZ / "web/assets/app.js").read_text()

    assert 'pedirConfirmacao(' in javascript
    assert 'Não dá para desfazer.' in javascript
    assert '#account-confirm-yes' in javascript


def test_exclusao_e_desvinculo_passam_pelas_funcoes_do_banco():
    javascript = (RAIZ / "web/assets/app.js").read_text()

    assert 'rpc("desvincular_meu_telegram")' in javascript
    assert 'rpc("excluir_minha_conta")' in javascript


def test_edicao_dispensa_as_credenciais_de_quem_ja_tem_sessao():
    javascript = (RAIZ / "web/assets/app.js").read_text()

    assert "function entrarNoModoEdicao()" in javascript
    assert "form.elements.senha.required = false" in javascript
