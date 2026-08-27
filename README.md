# Radar de Estágio

Agente que busca vagas de estágio todos os dias, avalia cada uma com IA contra o perfil do
usuário e entrega no Telegram só as compatíveis — ranqueadas e com os pontos a favor e contra de cada uma.

- Proposta completa: [`docs/proposta.md`](docs/proposta.md)
- Plano do MVP, passo a passo: [`docs/plano-mvp.md`](docs/plano-mvp.md)
- O que foi feito em cada passo: [`docs/passos-realizados.md`](docs/passos-realizados.md)
- Arquitetura e decisões: [`docs/arquitetura.md`](docs/arquitetura.md)
- Regras do projeto e estado atual: [`CLAUDE.md`](CLAUDE.md)
- Protótipo visual do painel da Fase 3: [`web/README.md`](web/README.md)

## Como funciona

```
Adzuna (vagas dos últimos 2 dias)
  → pré-filtro por regras (descarta o que não é estágio, exige sênior etc.)
  → Gemini avalia em lotes: nota 0–100, pontos a favor e contra, alerta de pegadinha
  → ranqueia e pega as 5 melhores
  → envia a mensagem no Telegram
```

Roda de duas formas:

- **No seu computador**, com as suas chaves, mandando para o **seu** Telegram.
- **Sozinho no GitHub Actions**, todo dia às 08:00 (Brasília), com as chaves cadastradas nos
  secrets do repositório, mandando para o Telegram de quem cadastrou.

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
| `ADZUNA_DIAS_RECENTES` | `2` | busca vagas publicadas nos últimos N dias |
| `QUANTIDADE_VAGAS_ENVIADAS` | `5` | quantas vagas vão na mensagem |

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
| `uv run python -m radar coletar` | lista as vagas da Adzuna | não |
| `uv run python -m radar avaliar` | avalia 3 vagas e imprime as notas | sim |
| `uv run python -m radar` | **fluxo completo**: coleta → avalia → envia no Telegram | sim |

Testes automatizados e lint (não usam chave nenhuma):

```bash
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

## 5. Execução automática no GitHub

O arquivo [`.github/workflows/radar-diario.yml`](.github/workflows/radar-diario.yml)
roda o fluxo completo todo dia às 11:00 UTC (08:00 em Brasília). O horário pode atrasar
alguns minutos — é normal no GitHub Actions.

As chaves vêm dos **secrets do repositório** (Settings → Secrets and variables →
Actions), com exatamente os mesmos nomes do `.env`: `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`,
`GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`. Só existe um conjunto de
secrets por repositório, então a mensagem diária vai para o Telegram de quem os cadastrou.

Para disparar na hora (teste ou demo):

1. Abra <https://github.com/babue0/RadarEstagio/actions>.
2. No menu da esquerda, clique em **Radar diário**.
3. **Run workflow** → **Run workflow**.
4. Em ~1 minuto o job fica verde e a mensagem chega no Telegram. Se ficar vermelho, abra
   o passo **Executar o radar** para ver o erro.

## Estrutura do código

```
radar/
  domain/        entidades (Vaga, Perfil, ResultadoMatch), contratos e perfil fixo do MVP
  collectors/    coleta de vagas (Adzuna)
  filtering/     pré-filtro por regras, antes da IA
  matching/      prompt, cliente do Gemini e avaliação em lotes
  notification/  formatação da mensagem e envio no Telegram
  pipeline.py    orquestra coleta → filtro → avaliação → envio
  __main__.py    comandos de linha de comando
tests/           testes automatizados (pytest)
web/             protótipo visual do painel da Fase 3 (HTML/CSS/JS estático, sem back-end)
```
