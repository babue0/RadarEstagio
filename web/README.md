# Painel web — protótipo visual

Mockup navegável do painel da **Fase 3** (roadmap em [`../docs/proposta.md`](../docs/proposta.md)).
Serve para discutir layout e fluxo com o grupo antes de comprometer arquitetura.

**Não é o produto.** Não tem back-end, não faz requisição nenhuma e nenhuma ação tem
efeito real — os dados em [`assets/data.js`](assets/data.js) são fictícios. O código do
`radar/` não depende deste diretório e não é afetado por ele.

## Como abrir

Abra `web/index.html` no navegador (duplo clique) ou sirva a pasta:

```bash
python -m http.server -d web 8000
```

E acesse <http://localhost:8000>.

## O que tem

HTML/CSS/JS puro, sem build e sem dependências. Roteamento por hash (`#/hoje`,
`#/historico`, ...).

| Tela | Conteúdo |
|---|---|
| Hoje | Vagas do dia ranqueadas, nota e motivo da IA, alerta de pegadinha, curtir/descartar |
| Histórico | Vagas de dias anteriores, com filtros |
| Mercado | Estatísticas: habilidades pedidas, modalidade, empresas |
| Perfil | Formulário do perfil (hoje fixo em `radar/domain/perfil_fixo.py`) |
| Configurações | Entrega no Telegram, janela de busca, fontes de vagas |

## Decisões de UI

- Escala de espaçamento única (`--space-1..8`) e tokens de cor em `assets/styles.css`;
  sem valores soltos.
- Cor por tipo de ação, consistente: azul = primária, vermelho = destrutiva; avisos em
  verde (sucesso), âmbar (atenção) e vermelho (erro).
- Localização sempre visível: título da tela, trilha (breadcrumb) e item de menu ativo.
- Todo clicável tem cor/`cursor: pointer`/estado de foco; nada de ação sem retorno
  (toasts em `aria-live`).
- Ícones sempre com rótulo de texto ao lado; um único set (linha, estilo Lucide) inline
  no `index.html`.
- Tema claro/escuro seguindo o do sistema, com alternância manual.
