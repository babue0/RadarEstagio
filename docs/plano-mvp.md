# Plano do MVP — Radar de Estágio (Fase 1)

## Contexto

O projeto está no zero: só existem `CLAUDE.md` (regras, stack e arquitetura) e `docs/proposta.md`.
A Fase 1 é fechar o ciclo de ponta a ponta com **uma fonte (Adzuna)**, **perfil fixo**, **matching
com Gemini**, **mensagem no Telegram** e **cron diário no GitHub Actions** — **sem banco**.

O plano abaixo é dividido em passos pequenos e independentes, cada um com um critério de
"funcionou" testável antes de seguir para o próximo. Passos sem dependência de chave de API vêm
primeiro, para que dê para avançar enquanto as contas ainda não existem.

Ao aprovar este plano, o primeiro ato é salvá-lo em `docs/plano-mvp.md` e commitar.

## Regras que valem em todos os passos

- Sem comentários no código; nomes autoexplicativos.
- Cada passo = um ou mais commits atômicos, sempre `add → commit → push`.
- Nenhum segredo hardcoded: tudo via variável de ambiente lida por `pydantic-settings`.
- Nenhum passo começa antes de o anterior estar verde (lint + testes + verificação manual).

## Estrutura final de pastas

```
RadarEstagio/
├── pyproject.toml
├── .env.example
├── .github/workflows/radar-diario.yml
├── docs/
│   ├── proposta.md
│   └── plano-mvp.md
├── radar/
│   ├── __init__.py
│   ├── __main__.py            entrypoint: python -m radar
│   ├── settings.py            variáveis de ambiente (pydantic-settings)
│   ├── pipeline.py            orquestra coleta → pré-filtro → matching → entrega
│   ├── domain/
│   │   ├── models.py          Vaga, Perfil, ResultadoMatch (pydantic)
│   │   ├── ports.py           Protocols: ColetorDeVagas, AvaliadorDeVagas, Notificador
│   │   └── perfil_fixo.py     o perfil único do MVP
│   ├── collectors/
│   │   └── adzuna.py
│   ├── filtering/
│   │   └── prefiltro.py
│   ├── matching/
│   │   ├── gemini.py
│   │   └── prompt.py
│   └── notification/
│       ├── formatador.py      mensagem pura (texto), sem rede
│       └── telegram.py        envio via Bot API
└── tests/
    ├── fixtures/adzuna_resposta.json
    ├── test_models.py
    ├── test_adzuna.py
    ├── test_prefiltro.py
    ├── test_gemini.py
    ├── test_formatador.py
    └── test_pipeline.py
```

---

## Passo 0 — Fundação do projeto

**O que fazer**
- `pyproject.toml` com `uv`: deps `httpx`, `pydantic`, `pydantic-settings`, `google-genai`;
  dev `ruff`, `pytest`, `pytest-httpx` (mock de HTTP) — Python 3.12+.
- Config do `ruff` (lint + format) e do `pytest` no próprio `pyproject.toml`.
- Pastas `radar/` (com `__init__.py` em cada camada) e `tests/`.
- `radar/settings.py`: classe `Settings(BaseSettings)` com `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`,
  `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `ADZUNA_DIAS_RECENTES` (default 2),
  `QUANTIDADE_VAGAS_ENVIADAS` (default 5).
- `.env.example` com todas as variáveis vazias (o `.gitignore` já ignora `.env` e libera `.env.example`).
- `radar/__main__.py` provisório que só carrega `Settings` e imprime quais variáveis estão ausentes.
- Salvar este plano em `docs/plano-mvp.md`.

**Como verificar**
- `uv sync` instala tudo.
- `uv run ruff check . && uv run ruff format --check .` verdes.
- `uv run pytest` roda (zero testes ainda, sem erro de coleta).
- `uv run python -m radar` imprime a lista de variáveis faltando sem quebrar.

**Commits sugeridos**: `pyproject + ruff`, `settings + .env.example`, `plano em docs/`.

---

## Passo 1 — Domínio (entidades e contratos)

**O que fazer**
- `domain/models.py`:
  - `Vaga`: `id_externo`, `fonte`, `titulo`, `empresa`, `localizacao`, `descricao`, `url`, `publicada_em`.
  - `Perfil`: `curso`, `periodo`, `habilidades: list[str]`, `cidade`, `modalidade` (remoto/presencial/hibrido/indiferente).
  - `ResultadoMatch`: `vaga`, `nota: int` (0–100), `motivo: str`, `alerta_pegadinha: str | None`.
- `domain/ports.py`: três `Protocol`s — `ColetorDeVagas.coletar() -> list[Vaga]`,
  `AvaliadorDeVagas.avaliar(vaga, perfil) -> ResultadoMatch`, `Notificador.enviar(texto)`.
- `domain/perfil_fixo.py`: função `perfil_do_mvp() -> Perfil` com os dados do usuário nº 1
  (preencher com o perfil real do grupo — placeholder até lá).

**Como verificar**
- `tests/test_models.py`: `ResultadoMatch` rejeita nota fora de 0–100; `Perfil` rejeita modalidade inválida.
- Camada `domain/` não importa nada além de `pydantic`/stdlib.

---

## Passo 2 — Coletor Adzuna

**O que fazer**
- `collectors/adzuna.py`: `ColetorAdzuna(settings, cliente_http)` implementando `ColetorDeVagas`.
  - Endpoint `https://api.adzuna.com/v1/api/jobs/br/search/1` com `app_id`, `app_key`,
    `what=estágio`, `category=it-jobs`, `max_days_old`, `results_per_page=50`, `content-type=application/json`.
  - Converte cada item do JSON em `Vaga` (`id`, `title`, `company.display_name`, `location.display_name`,
    `description`, `redirect_url`, `created`).
- Gravar uma resposta real (ou representativa) em `tests/fixtures/adzuna_resposta.json`.

**Como verificar**
- `tests/test_adzuna.py` com `pytest-httpx`: dado o fixture, retorna a lista de `Vaga` esperada;
  resposta vazia retorna lista vazia; HTTP 4xx levanta erro claro.
- Manual (quando houver chave): script `uv run python -m radar coletar` imprime N vagas reais com título e URL.

---

## Passo 3 — Pré-filtro por regras

**O que fazer**
- `filtering/prefiltro.py`: função pura `filtrar(vagas, perfil) -> list[Vaga]` que descarta:
  - título sem `estágio`/`estagiário`/`intern`;
  - título/descrição com `pleno`, `sênior`, `senior`, `especialista`, `coordenador`;
  - exigência explícita de anos de experiência ≥ 2 (regex simples);
  - localização incompatível quando `perfil.modalidade == presencial` (cidade diferente e sem "remoto").
- Cada regra é uma função pequena e nomeada; `filtrar` só as compõe.

**Como verificar**
- `tests/test_prefiltro.py`: um caso por regra (mantém/descarta), mais o caso "vaga limpa passa".

---

## Passo 4 — Matching com Gemini

**O que fazer**
- `matching/prompt.py`: função `montar_prompt(vaga, perfil) -> str` com instrução de recrutador,
  pedindo nota 0–100, motivo em uma frase e alerta de pegadinha (ou nulo).
- `matching/gemini.py`: `AvaliadorGemini(settings, cliente)` implementando `AvaliadorDeVagas`.
  - Modelo Flash (`gemini-2.5-flash` ou o Flash vigente — confirmar na doc na hora).
  - Saída estruturada: `response_mime_type="application/json"` + `response_schema` gerado de um
    modelo pydantic `AvaliacaoIA(nota, motivo, alerta_pegadinha)`; converte em `ResultadoMatch`.
  - Erro da API ou JSON inválido → exceção própria `ErroDeAvaliacao` (o pipeline decide pular a vaga).

**Como verificar**
- `tests/test_gemini.py`: cliente falso devolve JSON fixo → `ResultadoMatch` correto; JSON quebrado → `ErroDeAvaliacao`.
- Manual (com chave): `uv run python -m radar avaliar` avalia 1 vaga do fixture e imprime nota/motivo.

---

## Passo 5 — Formatação e envio no Telegram

**O que fazer**
- `notification/formatador.py`: `formatar_mensagem(resultados, data) -> str` — cabeçalho com a data,
  lista ranqueada `1.` a `N.` com título, empresa, nota, motivo, alerta (se houver) e link;
  mensagem de "nenhuma vaga hoje" quando a lista está vazia. Usa `parse_mode=HTML` com escape.
- `notification/telegram.py`: `NotificadorTelegram(settings, cliente_http)` implementando `Notificador`,
  `POST https://api.telegram.org/bot<token>/sendMessage` com `chat_id`, `text`, `parse_mode`,
  `disable_web_page_preview`.
  Respeitar limite de 4096 chars: dividir em várias mensagens se passar.

**Como verificar**
- `tests/test_formatador.py`: ordem por nota decrescente, alerta aparece só quando existe,
  caracteres HTML escapados, lista vazia gera a mensagem correta, divisão acima de 4096.
- Manual (com token + chat_id): `uv run python -m radar testar-telegram` envia "Radar OK" e chega no chat.

---

## Passo 6 — Pipeline e entrypoint

**O que fazer**
- `pipeline.py`: `executar(coletor, avaliador, notificador, perfil, quantidade)`:
  coletar → filtrar → avaliar cada vaga (pular as que falharem, registrando via `logging`) →
  ordenar por nota → cortar em `quantidade` → formatar → enviar.
- `__main__.py`: monta as dependências reais a partir de `Settings` e chama `executar`;
  subcomandos `coletar`, `avaliar`, `testar-telegram` (dos passos anteriores) e o padrão `rodar`.
  `argparse` da stdlib basta.

**Como verificar**
- `tests/test_pipeline.py`: com coletor/avaliador/notificador falsos, verifica que o texto enviado
  contém as top-N na ordem certa e que vaga com `ErroDeAvaliacao` é ignorada sem derrubar o run.
- Manual: `uv run python -m radar` com `.env` completo → mensagem real no Telegram com vagas reais.

---

## Passo 7 — Agendamento no GitHub Actions

**O que fazer**
- `.github/workflows/radar-diario.yml`:
  - `on: schedule: cron "0 11 * * *"` (11:00 UTC = 08:00 em Brasília) + `workflow_dispatch`
    (botão da demo ao vivo).
  - Passos: checkout → `astral-sh/setup-uv` → `uv sync` → `uv run python -m radar`.
  - Segredos via `secrets.*` mapeados para as mesmas variáveis do `.env.example`.
- Cadastrar os 5 secrets em *Settings → Secrets and variables → Actions* do repo.

**Como verificar**
- Disparar manualmente pelo `workflow_dispatch` → job verde → mensagem chega no Telegram.
- No dia seguinte, confirmar que o cron rodou sozinho às 8h.

---

## Passo 8 — README

**O que fazer**
- `README.md` curto: o que é, como rodar local (`uv sync`, `.env`), como funciona o cron,
  quais chaves são necessárias e onde obtê-las. Link para `docs/proposta.md` e `docs/plano-mvp.md`.

**Como verificar**
- Um colega consegue clonar e rodar seguindo só o README.

---

## Contas e chaves (paralelo, sem código)

Necessárias a partir do Passo 2 (manual), 4 (manual), 5 (manual) e 7 (obrigatório):

| Serviço | Onde | O que gera |
|---|---|---|
| Adzuna | developer.adzuna.com | `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` |
| Gemini | aistudio.google.com → API keys | `GEMINI_API_KEY` |
| Telegram | @BotFather → `/newbot` → `RadarEstagio_bot` | `TELEGRAM_BOT_TOKEN` |
| Chat ID | mandar `/start` pro bot e abrir `https://api.telegram.org/bot<token>/getUpdates` | `TELEGRAM_CHAT_ID` |

Os testes unitários de todos os passos rodam **sem** chave alguma; só as verificações manuais dependem delas.

## Ordem de dependência

```
0 → 1 → 2 ─┐
        3 ─┼→ 6 → 7 → 8
        4 ─┤
        5 ─┘
```

Passos 2, 3, 4 e 5 dependem só do 1 e podem ser feitos em qualquer ordem entre si.
