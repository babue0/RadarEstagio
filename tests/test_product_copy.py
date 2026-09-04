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


def test_aviso_de_privacidade_nao_promete_tela_que_nao_existe():
    html = (RAIZ / "web/index.html").read_text()

    assert "apagar sua conta pelo painel" not in html
    assert "edite seus dados na página de perfil" not in html
    assert "fale com a equipe do projeto" in html


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
