from pathlib import Path

RAIZ = Path(__file__).parent.parent


def test_landing_nao_promete_chegada_antecipada_ou_edicao_inexistente():
    html = (RAIZ / "web/index.html").read_text()

    assert "Chegue antes" not in html
    assert "você poderá editar depois" not in html
    assert "Vagas mais claras" in html


def test_documentacao_reflete_a_fase_atual_e_as_evidencias_recentes():
    plano = (RAIZ / "docs/plano-melhorias-rcd.md").read_text()
    pre_prd = (RAIZ / "docs/pre-prd.md").read_text()
    proposta = (RAIZ / "docs/proposta.md").read_text()

    assert "Fase 2 — MVP de validação com usuários, parcialmente implementada" in plano
    assert "259 testes automatizados passam" in pre_prd
    assert "703 vagas únicas" in pre_prd
    assert "aprende com o feedback" not in proposta
