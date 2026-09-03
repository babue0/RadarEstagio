# Radar de Estágio

Agente de IA que garimpa sites de vagas de estágio todos os dias e entrega, via Telegram,
apenas as oportunidades compatíveis com o perfil do usuário — ranqueadas e explicadas.

Resumo do produto e da proposta completa em `docs/proposta.md`.

## Fase atual: MVP de validação com usuários (Fase 2, em andamento)

Estado atual:

- Duas fontes de vagas somadas: Adzuna (API oficial gratuita) e Gupy (API interna do
  portal, sem chave, com modalidade estruturada)
- Banco Supabase com perfis, vagas, avaliações, envios e eventos de produto por usuário
- Cadastro web com conta, perfil estruturado e vínculo com o Telegram
- Matching de compatibilidade via IA (Gemini API ou Antigravity CLI/AGY)
- Entrega da mensagem ranqueada no Telegram
- Agendamento diário via GitHub Actions
- Deduplicação e histórico entre execuções quando o banco está configurado
- Ativação operacional registrada na primeira recomendação entregue
- Funil instrumentado da landing à primeira recomendação, com eventos web sob RLS e marcos
  autoritativos registrados por gatilhos do banco

Ainda não disponível: edição, pausa e retomada do perfil, feedback para ranking, painel web e
novas fontes além de Adzuna e Gupy.

## Stack

- **Linguagem**: Python
- **Coleta de vagas**: Adzuna API (oficial) e Gupy (API interna
  `employability-portal.gupy.io/api/v1/jobs`, sem chave, campo `workplaceType`). As fontes
  ativas vêm de `FONTES` (padrão `adzuna,gupy`) e são somadas por `ColetorComposto`, que
  ignora uma fonte fora do ar e só falha se nenhuma responder. Novas fontes só entram se a
  validação comprovar cobertura insuficiente. LinkedIn está fora de escopo (bloqueia coleta
  automatizada).
- **IA de matching**: Google Gemini (modelos Flash), com dois adapters: Gemini Developer
  API para CI/produção e Antigravity CLI (`agy`) para testes locais.
- **Notificação**: Telegram Bot API. Bot: `RadarEstagio_bot`.
- **Agendamento**: workflow manual do GitHub Actions disparado diariamente por cron-job.org.
- **Persistência**: PostgreSQL gerenciado (Supabase), opcional: com `DATABASE_URL` o job
  lê os usuários do banco e guarda vagas, notas e envios; sem ela roda com o perfil fixo e
  sem histórico. Acesso por `psycopg` com SQL puro; schema em `supabase/migrations/`.
  SQLite foi descartado — ver "Decisões técnicas".
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
- `storage/` — acesso a dados atrás dos contratos `RepositorioDeUsuarios` e
  `RepositorioDeAvaliacoes` do `domain/`: `postgres.py` (Supabase) e `memoria.py` (objeto
  nulo com o perfil fixo). `factory.py` escolhe pela presença de `DATABASE_URL`.
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

A Fase 1 não usava banco. O Passo 9 (Fase 2) adicionou o Supabase como opcional: tabelas
`perfis`, `vagas`, `avaliacoes`, `envios` e `eventos_produto`, todas com RLS; `perfis` limita
o usuário à própria linha e `eventos_produto` limita o navegador ao catálogo web permitido.
O pipeline só conhece `Repositorio`; a falha de leitura dos usuários é a única fatal,
erros ao enviar ou gravar de um usuário viram aviso. Nunca alterar tabela pelo painel — só
por migration em `supabase/migrations/`.

### Bibliotecas

Sem framework web: a aplicação é um script disparado por cron, não um serviço HTTP.

- `httpx` para chamadas HTTP (Adzuna, Gupy e Telegram)
- `psycopg` 3 para o PostgreSQL, SQL puro, sem ORM
- `google-genai` para o Gemini
- `agy` (dependência externa local) para executar o Antigravity CLI em modo headless
- `pydantic` para as entidades do `domain/` e para tipar a saída estruturada da IA
- `pydantic-settings` para configuração via variáveis de ambiente
- `ruff` para lint e formatação, `pytest` para testes

`python-telegram-bot` não entra em fase alguma: o bot só envia mensagens (uma requisição
HTTP simples). O único evento recebido, o `/start` do vínculo, chega por webhook a uma Edge
Function do Supabase, fora do `radar/`.

### Cadastro no site, não no bot

O cadastro conversacional pelo bot foi substituído por um site com conta. Motivos: dados
de perfil são estruturados (lista de habilidades, período, modalidade) e um formulário é
mais claro que uma conversa; o bot continua sem estado e sem máquina de conversa; o Supabase já
resolve conta (Auth) e banco de uma vez.

Fluxo: o usuário cria a conta no site → preenche o perfil → clica no botão do
Telegram, que abre `t.me/RadarEstagio_bot?start=<token>` com um token único da conta →
o Telegram chama o webhook (Edge Function do Supabase) com `/start <token>` → a função
grava o `chat_id` no perfil daquela conta. A partir daí o job diário lê os perfis com
`chat_id` do banco no lugar do `perfil_fixo` e envia uma mensagem por usuário.

O frontend é uma landing estática integrada ao Supabase. O contrato entre o site e o `radar/` é
o schema do banco: o site escreve `perfis`, o `radar/` lê
`perfis` e escreve `vagas` e `avaliacoes`. Nenhum dos dois expõe API para o outro. O
contrato completo para o front está em `docs/contrato-front.md`.

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

Fase 2 em andamento, após a conclusão da base técnica da Fase 1:

- Passos 0 a 8 concluídos: fundação (`uv`, `ruff`, `pytest`, `Settings`), domínio
  (`Vaga`, `Perfil`, `ResultadoMatch`, ports, perfil fixo), coletor da Adzuna com
  testes e verificação manual (`python -m radar coletar`), pré-filtro por regras
  (`filtering/prefiltro.py`), matching com Gemini API (`matching/gemini.py`) ou AGY local
  (`matching/agy.py`), ambos com saída estruturada de fatores; `matching/avaliacoes.py`
  calcula a nota com pesos de 45 para habilidades, 10 para curso, 10 para área, 15 para
  período/experiência, 10 para logística e 10 para área de interesse (01/09/2026): a IA
  classifica a vaga em subáreas de um catálogo fechado de 7 (`AreaDeInteresse` no domínio)
  e o fator compara com `perfis.areas_de_interesse` — match ganha o fator cheio; vaga sem
  subárea reconhecida fica com meio fator e também respeita o teto de 65 (só passa de 65
  quem é comprovadamente da área de interesse); mismatch zera o fator, limita a nota a 65 e põe o aviso
  "Fora das suas áreas de interesse" na mensagem (vaga de outra área preenche dia vazio,
  mas nunca passa na frente da área do candidato); perfil sem interesses não é penalizado. O curso também impõe teto
  (02/09/2026): incompatível limita a 35 (abaixo da nota mínima, sai da mensagem) com o
  aviso "Exige formação de outra área"; parcial limita a 75 — vaga operacional de fundos
  com Excel/Python/SQL chegou a 90 só pela stack genérica; o prompt trata lista de
  formações sem curso de computação como incompatível mesmo com "áreas afins". A migration
  `0006_areas_de_interesse.sql` foi aplicada ao projeto atual em 01/09/2026 e o cadastro web
  coleta o campo. A cobertura de requisitos é suavizada,
  `(1+atendidas)/(1+exigidas)`: requisito ausente do perfil vale como incerteza ("não
  informado"), nunca como veto — as travas de 60/70 pontos por habilidade ausente foram
  removidas em 31/08/2026 porque enterravam vagas boas (EPE Ciência de Dados a 48 por
  "faltar Power BI") enquanto anúncios sem stack ocupavam o topo. Idiomas e pacote Office
  não contam na cobertura (ninguém os cadastra no perfil), mas seguem visíveis na lista de
  requisitos. Vaga que não declara stack recebe cobertura neutra de 0.35 (~nota 65):
  entregável, porém atrás de vaga detalhada e parcialmente compatível. Tecnologias são
  comparadas por nomes normalizados e exatos, de modo que `Java` não corresponde a
  `JavaScript`. O fluxo foi verificado com
  `python -m radar avaliar`, e
  notificação no Telegram (`notification/formatador.py` monta a mensagem em HTML e
  divide acima de 4096 caracteres; `notification/telegram.py` envia; verificado com
  `python -m radar testar-telegram`) e pipeline (`pipeline.py`, comando padrão
  `python -m radar`, verificado com envio real de 5 vagas avaliadas pelo Gemini) e
  agendamento (`.github/workflows/radar-diario.yml` só com `workflow_dispatch`; quem
  dispara às 07:23 em Brasília é um job no cron-job.org chamando a API `dispatches` do
  GitHub com fine-grained token — o `schedule` nativo ficou 2 dias sem disparar e foi
  removido; os 5 secrets do repositório têm os mesmos nomes das variáveis do `.env`) e
  README com instalação, chaves, `.env`, comandos e disparo manual do workflow.
- Modelo Gemini padrão: `gemini-3.6-flash` (configurável por `GEMINI_MODELO`). O
  `gemini-2.5-flash` foi recusado pela API como indisponível para contas novas.
- Cota do Gemini: os limites variam por modelo, projeto e janela. Uma execução real recebeu
  HTTP 429 com limite 20 e indicação de nova tentativa após cerca de 60 segundos. Para
  reduzir consumo, a avaliação é feita em lotes: o adapter ativo avalia uma lista de vagas
  em uma única chamada (JSON com `id_vaga` por item), e `matching/lotes.py`
  (`AvaliadorEmLotes`) divide
  as vagas em lotes de `GEMINI_VAGAS_POR_LOTE` (padrão 10), reparte ao meio um lote que
  falhar até isolar a vaga com problema, reavalia sozinha a vaga que o modelo omitir e,
  em HTTP 429 (`CotaDeAvaliacaoExcedida`), lê o "retry in Ns" da mensagem, aguarda esse
  tempo (60 s se não vier; desiste se passar de 120 s, que indica cota diária) e repete o
  mesmo lote até 3 vezes antes de parar e devolver o que já tem. A cota gratuita do
  `gemini-3.6-flash` é de 20 requisições por minuto. O contrato
  `AvaliadorDeVagas.avaliar` recebe e devolve listas. Evitar rodar `avaliar`/`rodar`
  repetidamente sem necessidade.
- Melhoria pós-MVP: `Vaga.modalidade` (opcional) preenchida pela Gupy; o pré-filtro decide
  por ela quando existe e só usa regex no texto quando a fonte não informa. Duplicata entre
  fontes: fica a versão que informa modalidade e, em empate, a de descrição mais longa.
- Pendências da Fase 2: validar o produto com estudantes e decidir como tratar a cota do Gemini
  para vários usuários (billing ou Claude).
- Qualidade da mensagem (29/08/2026): `NOTA_MINIMA` (padrão 40) corta vagas fracas da
  mensagem — sem aprovadas, vai "Nenhuma vaga compatível"; o pré-filtro descarta título de
  área claramente fora de computação (`fora_da_area_de_tecnologia`); o prompt define
  "área de tecnologia" como computação e exclui engenharias tradicionais explicitamente.
- Cobertura das fontes (30/08/2026): a Adzuna classificava 93% das vagas brasileiras como
  categoria "Unknown", então `category=it-jobs` escondia quase tudo (55 vagas em 5 dias no
  país inteiro). O coletor agora usa `what_and=estágio` + `what_or=<termos de computação>`,
  sem categoria, até 4 páginas de 50, e repete a busca com `where=<cidade>` para cada cidade
  de perfil presencial ou híbrido (`collectors/factory.py::cidades_de_interesse`, cidades
  vindas do repositório em `__main__.py`). A localização vem de `location.area`
  (cidade, estado), então bairro não quebra o filtro de cidade. A Gupy deixou de buscar por
  termos no título: busca todos os estágios do país (até 10 páginas) e todos os da cidade
  (`city=`). Como o volume cresceu, `fora_da_area_de_tecnologia` passou a exigir sinal de
  computação no título ou, se o título for genérico, na descrição. Efeito medido: perfil
  Rio presencial saiu de 2 para 55 candidatas em um dia. Agregadores (Divulga Vagas,
  BuscarVagas) republicam o mesmo anúncio com "empresa" diferente; `remover_republicacoes`
  em `filtering/duplicatas.py` une vagas com mesmo título (sem sufixo "- Vaga") e cidade
  cujas 40 primeiras palavras da descrição coincidam em 80% (a Adzuna trunca em 500
  caracteres, por isso só o início conta; descrições com menos de 20 palavras nunca unem).
- Passo 9 (Fase 2) no código: banco Supabase opcional (`DATABASE_URL`), pipeline por
  usuário, `Usuario` no domínio, `storage/`.
- Passo 10 (Fase 2): webhook do `/start` em `supabase/functions/telegram-webhook/` (Edge
  Function em Deno/TypeScript, fora do `radar/`), publicada com `supabase functions deploy`
  e registrada no Telegram por `setWebhook` com `secret_token`; segredos
  `TELEGRAM_BOT_TOKEN` e `TELEGRAM_WEBHOOK_SECRET` em `supabase secrets`. Testada de ponta a
  ponta em 28/08/2026, republicada no projeto atual e retestada com um vínculo real em
  29/08/2026. Com o webhook ativo, `getUpdates` deixa de funcionar nesse bot.
- Passo 11 (Fase 2): landing integrada ao Supabase Auth e à tabela `perfis`, com criação e
  login por e-mail/senha, retomada depois da confirmação de e-mail, deep link do Telegram e
  detecção do vínculo ao voltar para a página. A migration `0002_permissoes_frontend.sql`
  restringe a escrita dos campos de vínculo ao webhook. Projeto atual:
  `xrhvjwemmylwbqgluebc` (`sa-east-1`). A `DATABASE_URL` do Actions já usa esse banco;
  pendência externa: configurar o redirect do Auth para `http://localhost:8000`.
- Passo 12 (Fase 2): ativação operacional definida como a primeira entrega bem-sucedida com ao
  menos uma recomendação. `perfis.ativado_em` é gravado uma única vez, na transação dos `envios`;
  `docs/metricas.md` separa esse marco da ativação de produto, que começará em `vaga_aberta`, e
  define a taxa operacional em 7 dias e o tempo mediano até a primeira entrega. A migration
  `0003_evento_ativacao.sql` foi aplicada ao projeto Supabase atual em 29/08/2026.
- O projeto `bnzogphdvpubtkcflcue` (`us-east-2`) foi criado por engano e não deve ser usado.
  Não o remover sem confirmar que nenhum recurso externo ainda aponta para ele.
- Contas criadas e credenciais configuradas no `.env` local (Adzuna e Telegram; Gemini
  somente quando `AVALIADOR=gemini_api`). O `.env` nunca é commitado; o GitHub Actions usa
  os secrets do repositório e o adapter padrão `gemini_api`.
- Passo 1 está mais avançado que o restante do plano previa: `perfil_fixo.py` já contém
  o perfil real do usuário nº 1.
