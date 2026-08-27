# Radar de Estágio

Agente de IA que garimpa sites de vagas de estágio todos os dias e entrega, via Telegram,
apenas as oportunidades compatíveis com o perfil do usuário — ranqueadas e explicadas.

Resumo do produto e da proposta completa em `docs/proposta.md`.

## Fase atual: MVP (Fase 1)

Escopo da Fase 1, conforme roadmap:

- Uma única fonte de vagas (Adzuna, API oficial gratuita)
- Perfil de usuário fixo (sem cadastro conversacional ainda)
- Matching de compatibilidade via IA (Gemini API ou Antigravity CLI/AGY)
- Entrega da mensagem ranqueada no Telegram
- Agendamento diário via GitHub Actions
- Sem banco de dados: a execução é sem estado. O papel de dedupe é coberto pelo filtro
  de data da Adzuna (apenas vagas publicadas nos últimos dias)

Fora do escopo da Fase 1 (fica para Fase 2/3): múltiplas fontes de vagas, banco com
histórico/dedupe, cadastro conversacional, múltiplos usuários, feedback curtir/descartar,
painel web.

## Stack

- **Linguagem**: Python
- **Coleta de vagas**: Adzuna API (oficial). Gupy (API interna) e Vagas.com/InfoJobs
  (scraping com requests + BeautifulSoup) entram nas fases seguintes. LinkedIn está
  fora de escopo (bloqueia coleta automatizada).
- **IA de matching**: Google Gemini (modelos Flash), com dois adapters: Gemini Developer
  API para CI/produção e Antigravity CLI (`agy`) para testes locais.
- **Notificação**: Telegram Bot API. Bot: `RadarEstagioBot`.
- **Agendamento**: GitHub Actions (cron diário), repositório público.
- **Persistência**: nenhuma na Fase 1. A partir da Fase 2, PostgreSQL gerenciado
  (Supabase). SQLite foi descartado — ver "Decisões técnicas".
- **Contas e chaves de API**: configuradas por variáveis de ambiente (`.env`, nunca
  commitado).

## Arquitetura

Arquitetura limpa, separando por responsabilidade:

- `domain/` — entidades e regras de negócio puras (Vaga, Perfil, Resultado de matching).
  Sem dependência de bibliotecas externas.
- `collectors/` — um módulo por fonte de vagas, cada um implementando a mesma interface
  de coleta. Fontes novas se plugam sem alterar o restante do sistema.
- `matching/` — adapters de IA e lógica de pontuação/justificativa. `factory.py` escolhe
  entre `AvaliadorGemini` e `AvaliadorAgy`; ambos implementam `AvaliadorDeVagas`.
- `notification/` — formatação e envio de mensagens (Telegram).
- `storage/` — acesso a dados, isolado atrás de uma interface de repositório definida no
  `domain/`. Não existe na Fase 1; entra na Fase 2 com PostgreSQL.
- `pipeline.py` (ou equivalente) — orquestra coleta → dedupe → pré-filtro → matching →
  entrega, sem conter lógica de negócio própria.

Módulos internos não dependem de detalhes de infraestrutura (API específica, formato de
mensagem, driver de banco) — dependem de interfaces do `domain/`.

## Decisões técnicas

### Banco de dados: PostgreSQL, não SQLite

A proposta original previa SQLite. Foi descartado por incompatibilidade com o modelo de
execução escolhido: o GitHub Actions provisiona uma máquina nova a cada execução e a
destrói ao terminar. SQLite é um arquivo em disco e não teria onde persistir entre as
execuções diárias.

As alternativas para contornar isso foram avaliadas e rejeitadas:

- Versionar o arquivo `.db` no repositório exigiria permissão de escrita para o job,
  incharia o histórico com blobs binários e — como o repositório é público — exporia
  perfis e `chat_id` de Telegram dos usuários a partir da Fase 2.
- `actions/cache` não é armazenamento durável: sofre evicção, e perder o histórico
  significa reenviar vagas já vistas.

A escolha é PostgreSQL gerenciado no **Supabase**, que a própria proposta já previa para
a fase do painel web — adotá-lo na Fase 2 evita duas migrações. `JSONB` acomoda o payload
cru das vagas e a saída estruturada da IA sem exigir mudança de schema a cada alteração
das fontes.

MySQL foi considerado e não oferece vantagem neste caso: suporte a JSON mais limitado e
opções gerenciadas gratuitas piores que as de PostgreSQL.

A Fase 1 não usa banco algum. Dedupe e histórico só entram na Fase 2, e o filtro por data
da Adzuna já restringe o resultado a vagas recentes.

### Bibliotecas

Sem framework web: a aplicação é um script disparado por cron, não um serviço HTTP.

- `httpx` para chamadas HTTP (Adzuna e Telegram)
- `google-genai` para o Gemini
- `agy` (dependência externa local) para executar o Antigravity CLI em modo headless
- `pydantic` para as entidades do `domain/` e para tipar a saída estruturada da IA
- `pydantic-settings` para configuração via variáveis de ambiente
- `ruff` para lint e formatação, `pytest` para testes

`python-telegram-bot` só entra na Fase 2, junto do cadastro conversacional — a Fase 1
apenas envia mensagens, o que é uma requisição HTTP simples.

### Seleção do avaliador de IA

`AVALIADOR` escolhe o adapter sem alterar o pipeline:

- `AVALIADOR=gemini_api` usa `AvaliadorGemini`, exige `GEMINI_API_KEY` e usa
  `GEMINI_MODELO` (padrão `gemini-3.6-flash`). É o padrão quando a variável não existe.
- `AVALIADOR=agy` usa `AvaliadorAgy`, não exige `GEMINI_API_KEY` e usa `AGY_MODELO`
  (padrão `gemini-3.6-flash-low`) e `AGY_TIMEOUT_SEGUNDOS` (padrão 300). Requer o comando
  `agy` instalado e autenticado localmente.

Para persistir a escolha, editar o `.env`:

```env
AVALIADOR=agy
AGY_MODELO=gemini-3.6-flash-low
```

Para trocar somente em uma execução, a variável do shell sobrescreve o `.env`:

```bash
AVALIADOR=agy uv run python -m radar avaliar
AVALIADOR=gemini_api uv run python -m radar avaliar
```

`uv run python -m radar verificar` mostra o adapter ativo. `avaliar` testa até três vagas
sem enviar mensagem; `uv run python -m radar` executa o fluxo completo e envia ao Telegram.
O GitHub Actions não define `AVALIADOR`, portanto continua no padrão `gemini_api`.

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
- **Conventional Commits** (conventionalcommits.org) em toda mensagem de commit:
  - Formato da primeira linha: `tipo(escopo): descrição`. Escopo é opcional e nomeia a
    camada ou módulo afetado (`collectors`, `settings`, `ci`...).
  - Tipos: `feat` (funcionalidade nova), `fix` (correção), `docs`, `test`, `refactor`
    (sem mudar comportamento), `perf`, `style` (formatação), `build` (dependências),
    `ci` (GitHub Actions), `chore` (manutenção que não se encaixa nos demais).
  - Descrição em português, minúscula, no presente do indicativo, sem ponto final,
    até 72 caracteres. Ex.: `feat(collectors): adiciona coletor da Adzuna`.
  - Corpo opcional, separado por linha em branco, explicando o *porquê* da mudança.
  - Mudança incompatível: `!` após o tipo/escopo (`feat(settings)!: ...`) e rodapé
    `BREAKING CHANGE: <explicação>`.
- **`.gitignore` sempre atualizado**: nunca commitar segredos (`.env`), bancos locais,
  ambientes virtuais ou artefatos de build.

## Estado do projeto

Fase 1 em andamento, seguindo `docs/plano-mvp.md`:

- Passos 0 a 8 concluídos: fundação (`uv`, `ruff`, `pytest`, `Settings`), domínio
  (`Vaga`, `Perfil`, `ResultadoMatch`, ports, perfil fixo), coletor da Adzuna com
  testes e verificação manual (`python -m radar coletar`), pré-filtro por regras
  (`filtering/prefiltro.py`), matching com Gemini API (`matching/gemini.py`) ou AGY local
  (`matching/agy.py`), ambos com saída estruturada e verificados com
  `python -m radar avaliar`, e
  notificação no Telegram (`notification/formatador.py` monta a mensagem em HTML e
  divide acima de 4096 caracteres; `notification/telegram.py` envia; verificado com
  `python -m radar testar-telegram`) e pipeline (`pipeline.py`, comando padrão
  `python -m radar`, verificado com envio real de 5 vagas avaliadas pelo Gemini) e
  agendamento (`.github/workflows/radar-diario.yml`: cron `0 11 * * *` = 08:00 em
  Brasília + `workflow_dispatch`; os 5 secrets do repositório têm os mesmos nomes das
  variáveis do `.env`) e README com instalação, chaves, `.env`, comandos e disparo
  manual do workflow.
- Modelo Gemini padrão: `gemini-3.6-flash` (configurável por `GEMINI_MODELO`). O
  `gemini-2.5-flash` foi recusado pela API como indisponível para contas novas.
- Cota do Gemini: os limites variam por modelo, projeto e janela. Uma execução real recebeu
  HTTP 429 com limite 20 e indicação de nova tentativa após cerca de 60 segundos. Para
  reduzir consumo, a avaliação é feita em lotes: o adapter ativo avalia uma lista de vagas
  em uma única chamada (JSON com `id_vaga` por item), e `matching/lotes.py`
  (`AvaliadorEmLotes`) divide
  as vagas em lotes de `GEMINI_VAGAS_POR_LOTE` (padrão 10), reparte ao meio um lote que
  falhar até isolar a vaga com problema, reavalia sozinha a vaga que o modelo omitir e,
  em HTTP 429 (`CotaDeAvaliacaoExcedida`), para e devolve o que já tem. O contrato
  `AvaliadorDeVagas.avaliar` recebe e devolve listas. Evitar rodar `avaliar`/`rodar`
  repetidamente sem necessidade.
- MVP completo. Pendências: nota mínima para entrar na mensagem; cota do Gemini para
  vários usuários (billing ou Claude); decisão do grupo sobre `.agents/skills`.
- Contas criadas e credenciais configuradas no `.env` local (Adzuna e Telegram; Gemini
  somente quando `AVALIADOR=gemini_api`). O `.env` nunca é commitado; o GitHub Actions usa
  os secrets do repositório e o adapter padrão `gemini_api`.
- Passo 1 está mais avançado que o restante do plano previa: `perfil_fixo.py` já contém
  o perfil real do usuário nº 1.
