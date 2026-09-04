# Radar de Estágio

Agente de IA que garimpa sites de vagas de estágio todos os dias e entrega, via Telegram,
apenas as oportunidades compatíveis com o perfil do usuário — ranqueadas e explicadas.

Resumo do produto em `docs/proposta.md`, arquitetura detalhada em `docs/arquitetura.md`,
histórico passo a passo em `docs/passos-realizados.md`.

## Fase atual: MVP de validação com usuários (Fase 2, em andamento)

Funcionando hoje: duas fontes de vagas somadas (Adzuna e Gupy), banco Supabase com perfis,
vagas, avaliações, envios e eventos de produto por usuário, cadastro web com conta e vínculo
com o Telegram, matching de compatibilidade por IA, entrega da mensagem ranqueada no Telegram,
agendamento diário, deduplicação e histórico entre execuções, ativação operacional registrada
na primeira recomendação entregue e funil instrumentado da landing à primeira recomendação.

Ainda não disponível: edição, pausa e retomada do perfil, feedback para ranking, painel web e
novas fontes além de Adzuna e Gupy.

Pendências da Fase 2: validar o produto com estudantes. A cota do Gemini deixou de ser pendência
em 03/09/2026: a extração passou a ser por vaga e reaproveitada entre usuários, então o custo não
cresce com a coorte e billing não é necessário para o piloto.

## Stack

Python; dependências em `pyproject.toml`. O que o manifesto e o código não dizem sozinhos:

- **Adzuna**: API oficial e gratuita, com chave.
- **Gupy**: API interna do portal (`employability-portal.gupy.io/api/v1/jobs`), sem chave, com
  modalidade estruturada no campo `workplaceType`. LinkedIn está fora de escopo: bloqueia
  coleta automatizada.
- **Fontes ativas** vêm de `FONTES` (padrão `adzuna,gupy`) e são somadas por `ColetorComposto`,
  que ignora uma fonte fora do ar e só falha se nenhuma responder. Fonte nova só entra se a
  validação comprovar cobertura insuficiente.
- **IA de extração**: Google Gemini (modelos Flash), com dois adapters — Gemini Developer API
  para CI/produção e Antigravity CLI (`agy`) para testes locais. `AVALIADOR` escolhe qual; o
  padrão é `gemini_api` e o GitHub Actions não define a variável, portanto segue nele. Para
  alternar, ver a skill `trocar-avaliador`. A IA **só extrai fatos da vaga**; quem compara com o
  perfil e calcula a nota é Python, sem IA.
- **Telegram**: bot `RadarEstagio_bot`; o job só envia mensagens. Cada vaga vai em uma mensagem
  própria, porque o teclado inline do Telegram é por mensagem e uma mensagem só com as sete vagas
  passaria do limite de 4096 caracteres, deixando os botões órfãos no último pedaço. Só a primeira
  mensagem do dia notifica; as demais vão com `disable_notification` para o dia continuar valendo
  um aviso só.
- **Link rastreável**: o link de cada vaga na mensagem passa pela Edge Function `ir`, que registra
  `vaga_aberta` e redireciona para a fonte. O endereço vem de `URL_DE_RASTREIO`; vazio ou sem
  banco, a mensagem volta a apontar direto para a vaga.
- **Feedback por botões**: cada recomendação leva 👍/👎/Candidatei-me com `callback_data` no
  formato `<acao>:<token do envio>` (no máximo 53 dos 64 bytes permitidos). O 👎 troca os botões
  pelos quatro motivos e o motivo escolhido entra nas `propriedades` do mesmo `vaga_irrelevante`.
  O feedback é só registrado: **não** altera ranking nesta fase.
- **Leitura do funil**: `python -m radar metricas` imprime, direto do banco, o funil da coorte dos
  últimos 30 dias, a quebra das recusas por motivo e o custo de extração por usuário ativado. As
  consultas equivalentes estão em `docs/metricas.md`.
- **Agendamento**: o workflow do GitHub Actions só tem `workflow_dispatch`. Quem dispara às
  07:23 de Brasília é um job no cron-job.org chamando a API `dispatches` com fine-grained
  token — o `schedule` nativo ficou 2 dias sem disparar e foi removido.
- **Persistência**: PostgreSQL gerenciado (Supabase), opcional. Com `DATABASE_URL` o job lê os
  usuários do banco e guarda vagas, notas e envios; sem ela roda com o perfil fixo e sem
  histórico.
- **Chaves de API**: por variável de ambiente (`.env`, nunca commitado). Os secrets do
  repositório têm os mesmos nomes das variáveis do `.env`.

## Arquitetura

As camadas de `radar/` estão detalhadas em `docs/arquitetura.md`. A regra que o código não
ensina sozinho: **módulos internos dependem de interfaces do `domain/`, nunca de detalhes de
infraestrutura** (API específica, formato de mensagem, driver de banco). `pipeline.py` orquestra
coleta → dedupe → pré-filtro → extração (uma vez, para todos) → pontuação por perfil → entrega,
sem lógica de negócio própria. Fonte nova se
pluga implementando a interface de coleta, sem alterar o restante do sistema. Sem abstrações
prematuras nem código para casos hipotéticos futuros.

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
`psycopg` 3 acessa o PostgreSQL com SQL puro, sem ORM.

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

Passos 0 a 14 concluídos — o que cada um entregou está em `docs/passos-realizados.md`. Abaixo
só o conhecimento operacional que não dá para reconstituir lendo o código.

### Cota e modelo do Gemini

- Padrão `gemini-3.6-flash` (`GEMINI_MODELO`). O `gemini-2.5-flash` foi recusado pela API como
  indisponível para contas novas.
- A cota gratuita do `gemini-3.6-flash` é de 20 requisições por minuto, mas os limites variam
  por modelo, projeto e janela. Por isso a extração vai em lotes (`GEMINI_VAGAS_POR_LOTE`,
  padrão 10), com repartição do lote que falha e espera pelo "retry in Ns" do 429; acima de
  120 s a espera indica cota diária e o job desiste devolvendo o que já tem.
- **O custo não cresce com o número de usuários** (03/09/2026). O prompt não contém perfil, então
  cada vaga é extraída uma vez e a extração serve todos. Ela fica em `vagas.extracao` (JSONB), de
  modo que reexecução no mesmo dia ou usuário novo entrando não gastam cota. Antes eram cerca de
  6 requisições por usuário por dia: 20 estudantes estouravam a cota e o job morria no timeout de
  15 minutos, sempre deixando sem mensagem quem entrou por último, porque a fila é ordenada por
  `criado_em`. O resumo de cada execução informa quantas requisições foram gastas, e
  `test_dobrar_os_usuarios_nao_dobra_as_vagas_extraidas` impede que a propriedade se perca.
- **Evitar rodar `avaliar`/`rodar` repetidamente sem necessidade.**

### Pontuação: por que os pesos são estes

Pesos em `matching/avaliacoes.py`. O que motivou cada trava:

- **Cobertura de requisitos suavizada**, `(1+atendidas)/(1+exigidas)`: requisito ausente do
  perfil vale como incerteza ("não informado"), nunca como veto. As travas de 60/70 pontos por
  habilidade ausente foram removidas em 31/08/2026 porque enterravam vagas boas (EPE Ciência de
  Dados a 48 por "faltar Power BI") enquanto anúncios sem stack ocupavam o topo.
- **Vaga que não declara stack** recebe cobertura neutra de 0.35 (~nota 65): entregável, porém
  atrás de vaga detalhada e parcialmente compatível.
- **Idiomas e pacote Office não contam na cobertura** (ninguém os cadastra no perfil), mas
  seguem visíveis na lista de requisitos. As variantes normalizam antes da comparação
  (03/09/2026): "Microsoft Excel" vira `excel` e "Google Sheets" vira `planilhas`. Antes só o
  nome exato era ignorado e a variante pesava — uma vaga de dados caiu para 68 penalizada por
  Google Docs, Drive e Excel. A normalização é por alias, não por pedaço de palavra, para
  `WordPress` não virar `Word`.
- **Tecnologias comparadas por nome normalizado e exato**, de modo que `Java` não corresponde a
  `JavaScript`.
- **Área de interesse** (01/09/2026): a IA classifica a vaga em subáreas de um catálogo fechado
  de 7 (`AreaDeInteresse` no domínio) e o fator compara com `perfis.areas_de_interesse`. Match
  ganha o fator cheio; vaga sem subárea reconhecida fica com meio fator e respeita o teto de 65
  (só passa de 65 quem é comprovadamente da área de interesse); mismatch zera o fator, limita a
  nota a 65 e põe o aviso "Fora das suas áreas de interesse" na mensagem — vaga de outra área
  preenche dia vazio, mas nunca passa na frente da área do candidato. Perfil sem interesses não
  é penalizado.
- **Curso** (02/09/2026): incompatível limita a 35 (abaixo da nota mínima, sai da mensagem) com
  o aviso "Exige formação de outra área"; parcial limita a 75 — vaga operacional de fundos com
  Excel/Python/SQL chegou a 90 só pela stack genérica. Desde 03/09/2026 quem decide o nível é
  `matching/compatibilidade.py`, com um catálogo fechado de cursos de computação, e não mais o
  julgamento do modelo: a IA extrai `cursos_aceitos` e o Python compara. Curso que o catálogo não
  reconhecer cai como incompatível — é o ponto mais frágil da mudança.
- **Pontos a favor e contra são gerados da comparação** (03/09/2026), não escritos pela IA.
  Sobraram "Curso compatível", "Período mínimo incompatível" e "Exige experiência prévia", porque
  as habilidades já aparecem na lista de requisitos e duplicavam. `alerta_pegadinha` continua
  vindo do modelo.
- **Viés conhecido, decidido em 03/09/2026 a não corrigir antes do piloto**: anúncio que declara
  uma tecnologia só e é atendido tira 100, enquanto um que declara cinco e atende três tira 85 —
  a suavização dá 1.0 cravado com 1 de 1. Quanto mais honesto o anúncio, pior a nota. As duas
  correções possíveis e o sinal que reverte a decisão estão na seção 7 de
  `docs/auditoria-rcd.md`. **Não ajustar peso sem `vaga_irrelevante` real.**

### Qualidade da mensagem e do pré-filtro

- `NOTA_MINIMA` (padrão 40) corta vagas fracas da mensagem. Sem aprovadas, o estudante recebe
  que nada compatível apareceu e que a busca volta amanhã: silêncio total pareceria serviço
  morto. Depois de `DIAS_DE_SILENCIO_ATE_AVISAR` dias sem nenhuma recomendação, e no máximo uma
  vez por período, a mesma mensagem ganha um parágrafo sugerindo ampliar cidade ou modalidade —
  parágrafo, e não segunda mensagem, para não notificar duas vezes no mesmo dia.
- `fora_da_area_de_tecnologia` exige sinal de computação no título ou, se o título for genérico,
  na descrição. O prompt define "área de tecnologia" como computação e exclui engenharias
  tradicionais explicitamente.

### Cobertura das fontes (30/08/2026)

A Adzuna classificava 93% das vagas brasileiras como categoria "Unknown", então `category=it-jobs`
escondia quase tudo (55 vagas em 5 dias no país inteiro). A busca passou a ser por termos, sem
categoria, repetida por cidade de perfil presencial ou híbrido; a localização vem de
`location.area` (cidade, estado), então bairro não quebra o filtro de cidade. A Gupy deixou de
buscar por termos no título e traz todos os estágios do país e da cidade. Efeito medido: perfil
Rio presencial saiu de 2 para 55 candidatas em um dia.

Agregadores (Divulga Vagas, BuscarVagas) republicam o mesmo anúncio com "empresa" diferente:
`remover_republicacoes` em `filtering/duplicatas.py` une vagas com mesmo título e cidade cujas 40
primeiras palavras da descrição coincidam em 80% — só o início conta porque a Adzuna trunca a
descrição em 500 caracteres. Duplicata entre fontes: fica a versão que informa modalidade e, em
empate, a de descrição mais longa.

### Supabase e Telegram: fatos operacionais

- Projeto ativo: **`xrhvjwemmylwbqgluebc` (`sa-east-1`)**. A `DATABASE_URL` do Actions já usa
  esse banco.
- O projeto **`bnzogphdvpubtkcflcue` (`us-east-2`) foi criado por engano e não deve ser usado.**
  Não o remover sem confirmar que nenhum recurso externo ainda aponta para ele.
- **Nunca alterar tabela pelo painel do Supabase** — só por migration em `supabase/migrations/`.
- Com o webhook do `/start` ativo, **`getUpdates` deixa de funcionar nesse bot**.
- **`token_vinculo` é de uso único**: o webhook grava o `chat_id` e troca o token na mesma
  atualização, então link vazado não vincula o chat de outra pessoa. O token que o site leu antes
  do clique deixa de valer depois do vínculo.
- Pendência externa: configurar o redirect do Auth para `http://localhost:8000`.
- No pipeline, a falha de leitura dos usuários é a única fatal; erros ao enviar ou gravar de um
  usuário viram aviso.
- **A avaliação é gravada antes do envio** e os `envios` depois: falha do Telegram não descarta o
  que a IA já custou. Falhas seguidas incrementam `perfis.falhas_de_envio` e, ao atingir
  `FALHAS_DE_ENVIO_ATE_PAUSAR`, o perfil sai de `ativo` emitindo `entregas_pausadas`.
- **Toda execução se reporta** ao `TELEGRAM_CHAT_ID`, que com banco passa a ser o chat de
  operação: usuários ativos, quantos receberam recomendação, vagas enviadas e requisições. Kill
  por timeout, que o Python não consegue reportar, é coberto pelo passo `if: failure()` do
  workflow.
- **Cada linha de `envios` tem um `token` único**, gerado em Python antes do envio porque a
  mensagem precisa do link antes de a linha existir. Envio que falha ao ser gravado deixa um token
  órfão, e a Edge Function `ir` trata isso redirecionando para a landing.
- Ativação operacional = primeira entrega bem-sucedida com ao menos uma recomendação;
  `perfis.ativado_em` é gravado uma única vez, na transação dos `envios`. `docs/metricas.md`
  separa esse marco da ativação de produto.
- `domain/perfil_fixo.py` é um perfil **sintético** (`perfil_de_exemplo`), usado só quando não há
  `DATABASE_URL`. O repositório é público: nunca colocar ali dados reais de ninguém.
