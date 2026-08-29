# Radar de Estágio

Agente que busca vagas de estágio todos os dias, avalia cada uma com IA contra o perfil do
usuário e entrega no Telegram só as compatíveis — ranqueadas e com os pontos a favor e contra de cada uma.

- Proposta completa: [`docs/proposta.md`](docs/proposta.md)
- Plano do MVP, passo a passo: [`docs/plano-mvp.md`](docs/plano-mvp.md)
- O que foi feito em cada passo: [`docs/passos-realizados.md`](docs/passos-realizados.md)
- Arquitetura e decisões: [`docs/arquitetura.md`](docs/arquitetura.md)
- Evento de ativação e métricas: [`docs/metricas.md`](docs/metricas.md)
- Regras do projeto e estado atual: [`CLAUDE.md`](CLAUDE.md)
- Landing page e decisões de frontend: [`web/README.md`](web/README.md)

## Como funciona

```
Adzuna + Gupy (vagas dos últimos 5 dias)
  → remove duplicatas entre as fontes (título + empresa)
  → pré-filtro por regras (descarta o que não é estágio, exige sênior etc.)
  → Gemini avalia em lotes: nota 0–100, pontos a favor e contra, alerta de pegadinha
  → ranqueia e pega as 5 melhores
  → envia a mensagem no Telegram
```

Com banco configurado (`DATABASE_URL`), o mesmo fluxo roda **para cada usuário** cadastrado
no Supabase: pré-filtro com o perfil dele, sem repetir vaga que ele já recebeu, sem mandar ao
Gemini vaga que já tem nota guardada, e a mensagem vai para o Telegram dele. Sem banco, usa o
perfil fixo do código e o `TELEGRAM_CHAT_ID` do `.env`.

Roda de duas formas:

- **No seu computador**, com as suas chaves, mandando para o **seu** Telegram.
- **Sozinho no GitHub Actions**, todo dia às 07:23 (Brasília), com as chaves cadastradas nos
  secrets do repositório.

## Frontend

O escopo confirmado do frontend é uma landing page que apresenta o Radar e coleta o perfil do
estudante. Não há dashboard planejado no momento: a experiência recorrente continua concentrada
no Telegram.

Decisões atuais:

- HTML, CSS e JavaScript, sem framework ou etapa de build;
- conta por e-mail e senha com Supabase Auth;
- formulário com curso, período, habilidades, cidade e modalidade preferida, salvo diretamente
  na tabela `perfis` sob RLS;
- vínculo com o Telegram por link do bot contendo token temporário, sem pedir `@username` ou
  `chat_id` no formulário;
- React, Next.js ou outro framework só serão avaliados novamente se surgir uma necessidade real
  de interface mais complexa.

O perfil é persistido no Supabase depois da autenticação. Quando a confirmação de e-mail está
ativada, o navegador guarda temporariamente apenas os campos do perfil até o usuário voltar pelo
link de confirmação. Veja a configuração em [`web/README.md`](web/README.md).

## 1. Instalar (na ordem)

### 1.1 Git e o repositório

```bash
git clone https://github.com/babue0/RadarEstagio.git
cd RadarEstagio
```

### 1.2 `uv` (gerenciador de Python e dependências)

Não precisa instalar Python antes: o `uv` baixa a versão certa sozinho.

macOS / Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows (PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Feche e abra o terminal de novo. Confira com `uv --version`.

### 1.3 Dependências do projeto

```bash
uv sync
```

Cria a pasta `.venv` e instala tudo. Não precisa ativar o ambiente: todo comando é rodado
com `uv run ...`.

## 2. Pegar as chaves

Cada pessoa cria as **suas** chaves. Nunca compartilhe chave no chat do grupo nem
commite o `.env`.

### 2.1 Adzuna (fonte das vagas)

1. Crie uma conta em <https://developer.adzuna.com/signup>.
2. Em *Dashboard* aparecem **Application ID** e **Application Key**.

A **Gupy**, a segunda fonte, não precisa de chave: o projeto usa a API pública do portal.

### 2.2 Avaliador por IA

O projeto aceita dois adapters, escolhidos por `AVALIADOR`:

- `gemini_api`: chama a Gemini Developer API diretamente; é o padrão e funciona no CI.
- `agy`: executa o Antigravity CLI local em modo headless; indicado para testes locais.

Para usar a API direta:

1. Acesse <https://aistudio.google.com/app/apikey> com uma conta Google.
2. **Create API key** → copie a chave.

Os limites dependem do modelo e do projeto e podem incluir requisições por minuto e por dia.

Para usar AGY, instale o comando `agy`, autentique uma vez em uma sessão interativa e confirme
o modelo com `agy models`. Esse modo usa as cotas/créditos do Antigravity, não a cota da Gemini
Developer API.

### 2.3 Telegram (bot + seu chat)

Você cria o **seu próprio bot** — cada pessoa tem o seu, com o próprio token.

1. No Telegram, abra o **@BotFather** e mande `/newbot`.
2. Ele pede um nome de exibição (qualquer um) e um username terminando em `bot`
   (ex.: `meu_radar_estagio_bot`).
3. Ele responde com o **token**, no formato `123456789:AAF...`. Esse é o
   `TELEGRAM_BOT_TOKEN`.
4. Abra a conversa com o bot que você acabou de criar e mande **`/start`**. Sem isso o
   bot não consegue te enviar mensagem.
5. Descubra o seu **chat id** abrindo no navegador (troque `<TOKEN>` pelo token):

   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```

   Procure `"chat":{"id":123456789,...}`. Esse número é o `TELEGRAM_CHAT_ID`.
   Se aparecer `"result":[]`, mande `/start` de novo e recarregue a página.
   Se aparecer erro 409, é porque esse bot tem webhook registrado (seção 7); nesse caso o
   `chat_id` vem pelo vínculo, não por aqui.

## 3. Configurar o `.env`

Na raiz do projeto, copie o modelo e preencha:

```bash
cp .env.example .env
```

O `.env` fica assim (sem aspas, sem espaço em volta do `=`):

```
ADZUNA_APP_ID=seu_application_id
ADZUNA_APP_KEY=sua_application_key
AVALIADOR=agy
AGY_MODELO=gemini-3.6-flash-low
GEMINI_API_KEY=
TELEGRAM_BOT_TOKEN=123456789:AAF...
TELEGRAM_CHAT_ID=123456789
```

Adzuna e Telegram são sempre obrigatórios. `GEMINI_API_KEY` só é obrigatória quando
`AVALIADOR=gemini_api`. As demais variáveis têm valor padrão:

| Variável | Padrão | O que faz |
|---|---|---|
| `AVALIADOR` | `gemini_api` | seleciona `gemini_api` ou `agy` |
| `GEMINI_MODELO` | `gemini-3.6-flash` | modelo do Gemini |
| `GEMINI_VAGAS_POR_LOTE` | `10` | vagas avaliadas por requisição |
| `AGY_MODELO` | `gemini-3.6-flash-low` | modelo usado pelo Antigravity CLI |
| `AGY_TIMEOUT_SEGUNDOS` | `300` | tempo máximo de uma execução do AGY |
| `FONTES` | `adzuna,gupy` | fontes consultadas, separadas por vírgula |
| `DIAS_RECENTES` | `5` | busca vagas publicadas nos últimos N dias |
| `QUANTIDADE_VAGAS_ENVIADAS` | `5` | quantas vagas vão na mensagem |
| `NOTA_MINIMA` | `40` | vaga com nota abaixo disso não entra na mensagem |
| `DATABASE_URL` | vazio | string do Supabase; vazio = perfil fixo, sem histórico (seção 6) |

O `.env` está no `.gitignore` e nunca vai para o GitHub.

## 4. Rodar

Confira a configuração primeiro:

```bash
uv run python -m radar verificar
```

Se faltar alguma variável, ele lista quais. Depois, teste cada parte:

| Comando | O que faz | Usa IA? |
|---|---|---|
| `uv run python -m radar testar-telegram` | manda "Radar OK" para o seu chat | não |
| `uv run python -m radar coletar` | lista as vagas de todas as fontes, sem duplicatas | não |
| `uv run python -m radar avaliar` | avalia 3 vagas e imprime as notas | sim |
| `uv run python -m radar` | **fluxo completo**: coleta → avalia → envia no Telegram | sim |

Testes automatizados e lint (não usam chave nenhuma):

```bash
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

## 5. Execução automática no GitHub

O arquivo [`.github/workflows/radar-diario.yml`](.github/workflows/radar-diario.yml)
roda o fluxo completo. Quem dispara todo dia às 07:23 (Brasília) é um cron externo no
[cron-job.org](https://cron-job.org), que chama a API do GitHub
(`POST /repos/babue0/RadarEstagio/actions/workflows/radar-diario.yml/dispatches`, body
`{"ref":"main"}`) com um *fine-grained token* de permissão **Actions: Read and write**.
O `schedule` nativo do GitHub Actions foi removido: ficou dois dias sem disparar nenhuma vez.

As chaves vêm dos **secrets do repositório** (Settings → Secrets and variables →
Actions), com exatamente os mesmos nomes do `.env`: `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`,
`GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` e, com banco, `DATABASE_URL`.
Sem `DATABASE_URL`, a mensagem diária vai para o Telegram de quem cadastrou o
`TELEGRAM_CHAT_ID`; com ele, vai para cada usuário do banco.

Para disparar na hora (teste ou demo):

1. Abra <https://github.com/babue0/RadarEstagio/actions>.
2. No menu da esquerda, clique em **Radar diário**.
3. **Run workflow** → **Run workflow**.
4. Em ~1 minuto o job fica verde e a mensagem chega no Telegram. Se ficar vermelho, abra
   o passo **Executar o radar** para ver o erro.

## 6. Banco de dados (opcional, Fase 2)

O banco guarda os perfis dos usuários (com o `chat_id` de cada um), as vagas, as notas e o
que já foi enviado. É o que permite vários usuários e evita repetir vaga entre dias.

1. Crie um projeto em <https://supabase.com> (região São Paulo) e guarde a senha do banco.
2. Instale a CLI e ligue-a ao projeto:

   ```bash
   brew install supabase/tap/supabase
   supabase login
   supabase link --project-ref <ref do projeto>
   supabase db push
   ```

   O `db push` aplica [`supabase/migrations/`](supabase/migrations/) e cria as tabelas
   `perfis`, `vagas`, `avaliacoes` e `envios`. Nunca crie ou altere tabelas pelo painel:
   a migration é o contrato entre o site e o radar.
3. Em **Project Settings → Database**, copie a string **Session pooler** (o GitHub Actions só
   tem IPv4) e coloque em `DATABASE_URL` no `.env`.
4. Enquanto o site não existe, cadastre um usuário na mão: **Authentication → Add user** e,
   no **Table Editor**, uma linha em `perfis` com `user_id` desse usuário, o perfil e
   `telegram_chat_id`. Perfil sem `telegram_chat_id` ou com `ativo = false` é ignorado.
5. `uv run python -m radar verificar` deve mostrar `Banco: conectado, N usuários ativos`.
6. Para o Actions usar o banco, crie o secret `DATABASE_URL`.

## 7. Webhook do vínculo com o Telegram (opcional, Fase 2)

Quem faz o site deve ler [`docs/contrato-front.md`](docs/contrato-front.md): o que gravar
em `perfis`, permissões e o botão do Telegram.

Com o banco, o `chat_id` de cada usuário passa a ser gravado pelo próprio Telegram: o site
abre `t.me/RadarEstagio_bot?start=<token_vinculo>` e o bot chama a Edge Function
[`supabase/functions/telegram-webhook/`](supabase/functions/telegram-webhook/), que grava o
`chat_id` no perfil daquele token. Só quem administra o bot precisa fazer isto, uma vez:

1. Invente um segredo (`openssl rand -hex 24`) e coloque em `TELEGRAM_WEBHOOK_SECRET` no
   `.env`. O Telegram manda esse valor em toda chamada e a função rejeita quem não o tem.
2. Publique a função e os segredos:

   ```bash
   supabase functions deploy telegram-webhook
   supabase secrets set TELEGRAM_BOT_TOKEN=... TELEGRAM_WEBHOOK_SECRET=...
   ```

3. Registre o webhook (troque `<TOKEN>`, `<REF>` e `<SEGREDO>`):

   ```
   https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<REF>.supabase.co/functions/v1/telegram-webhook&secret_token=<SEGREDO>
   ```

   `getWebhookInfo` no lugar de `setWebhook` mostra se ficou registrado.
4. Para testar sem o site: no Table Editor, copie o `token_vinculo` do seu perfil, apague o
   `telegram_chat_id`, abra `https://t.me/RadarEstagio_bot?start=<token>` e aperte Start.
   O bot responde "Telegram vinculado!" e a coluna volta preenchida.

Os testes da função rodam com `deno test` dentro da pasta (`brew install deno`).

## Estrutura do código

```
radar/
  domain/        entidades (Vaga, Perfil, Usuario, ResultadoMatch), contratos e perfil fixo
  collectors/    coleta de vagas (Adzuna, Gupy) e o composto que soma as fontes
  filtering/     remoção de duplicatas e pré-filtro por regras, antes da IA
  matching/      prompt, cliente do Gemini e avaliação em lotes
  notification/  formatação da mensagem e envio no Telegram
  storage/       repositórios: Postgres (Supabase) ou em memória (perfil fixo)
  pipeline.py    orquestra coleta → filtro → avaliação → envio, por usuário
  __main__.py    comandos de linha de comando
supabase/        migrations do banco (schema versionado) e a Edge Function do webhook
tests/           testes automatizados (pytest)
web/             landing page e cadastro demonstrativo (HTML/CSS/JS estático, sem back-end)
```
