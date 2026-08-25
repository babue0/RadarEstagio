# Radar de Estágio

Agente de IA que garimpa sites de vagas de estágio todos os dias e entrega, via Telegram,
apenas as oportunidades compatíveis com o perfil do usuário — ranqueadas e explicadas.

Resumo do produto e da proposta completa em `docs/proposta.md`.

## Fase atual: MVP (Fase 1)

Escopo da Fase 1, conforme roadmap:

- Uma única fonte de vagas (Adzuna, API oficial gratuita)
- Perfil de usuário fixo (sem cadastro conversacional ainda)
- Matching de compatibilidade via IA (Gemini)
- Entrega da mensagem ranqueada no Telegram
- Agendamento diário via GitHub Actions

Fora do escopo da Fase 1 (fica para Fase 2/3): múltiplas fontes de vagas, banco com
histórico/dedupe, cadastro conversacional, múltiplos usuários, feedback curtir/descartar,
painel web.

## Stack

- **Linguagem**: Python
- **Coleta de vagas**: Adzuna API (oficial). Gupy (API interna) e Vagas.com/InfoJobs
  (scraping com requests + BeautifulSoup) entram nas fases seguintes. LinkedIn está
  fora de escopo (bloqueia coleta automatizada).
- **IA de matching**: Google Gemini (modelos Flash), camada gratuita. Migração para
  Claude Haiku 4.5 é opção futura caso a qualidade exija.
- **Notificação**: Telegram Bot API. Bot: `RadarEstagioBot`.
- **Agendamento**: GitHub Actions (cron diário), repositório público.
- **Persistência**: SQLite (Supabase entra só na fase com painel web).
- **Contas e chaves de API**: ainda não configuradas — usar variáveis de ambiente
  (`.env`, nunca commitado) quando forem definidas.

## Arquitetura

Arquitetura limpa, separando por responsabilidade:

- `domain/` — entidades e regras de negócio puras (Vaga, Perfil, Resultado de matching).
  Sem dependência de bibliotecas externas.
- `collectors/` — um módulo por fonte de vagas, cada um implementando a mesma interface
  de coleta. Fontes novas se plugam sem alterar o restante do sistema.
- `matching/` — cliente de IA e lógica de pontuação/justificativa. Trocar de provedor
  de IA (Gemini → Claude) deve significar trocar apenas esta camada.
- `notification/` — formatação e envio de mensagens (Telegram).
- `storage/` — acesso a dados (SQLite), isolado atrás de uma interface de repositório.
- `pipeline.py` (ou equivalente) — orquestra coleta → dedupe → pré-filtro → matching →
  entrega, sem conter lógica de negócio própria.

Módulos internos não dependem de detalhes de infraestrutura (API específica, formato de
mensagem, driver de banco) — dependem de interfaces do `domain/`.

## Regras do projeto (obrigatórias)

- **Nunca usar comentários no código.** Nomes de variáveis/funções/classes devem ser
  autoexplicativos.
- **Código organizado e com arquitetura limpa**, seguindo a separação de camadas acima.
  Sem abstrações prematuras nem código para casos hipotéticos futuros.
- **Repositório GitHub público.**
- **Claude/IA nunca deve aparecer como contribuidor, autor ou co-autor.** Commits usam
  exclusivamente a identidade git já configurada do usuário — nunca incluir assinatura,
  menção ou "Co-Authored-By" de Claude/Anthropic nos commits.
- **Commits atômicos**: cada commit representa uma mudança coesa e completa. Sempre
  seguir o ciclo `git add` → `git commit` → `git push` ao final de um commit.
- **`.gitignore` sempre atualizado**: nunca commitar segredos (`.env`), bancos locais,
  ambientes virtuais ou artefatos de build.

## Estado do projeto

- Fase 1 (MVP) ainda não implementada — este `CLAUDE.md` e a estrutura de convenções
  foram criados primeiro.
- Contas e chaves (Adzuna, Gemini, Telegram) serão configuradas depois; até lá, qualquer
  código que dependa delas deve ler de variáveis de ambiente, nunca hardcoded.
