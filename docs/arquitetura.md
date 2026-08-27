# Arquitetura do Radar de Estágio

Como o sistema é organizado, por que foi organizado assim e quais decisões foram tomadas no
caminho. O histórico passo a passo está em [`passos-realizados.md`](passos-realizados.md).

## Em uma frase

Um script Python, disparado uma vez por dia pelo GitHub Actions, que coleta vagas, filtra,
avalia com IA e envia uma mensagem no Telegram — **sem servidor e sem banco de dados**.

## O fluxo

```
┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐
│  coletar   │ → │ pré-filtrar│ → │  avaliar   │ → │  ranquear  │ → │   enviar   │
│  (Adzuna)  │   │  (regras)  │   │  (Gemini)  │   │  (top N)   │   │ (Telegram) │
└────────────┘   └────────────┘   └────────────┘   └────────────┘   └────────────┘
   ~15 vagas        ~14 vagas       2 requisições      5 vagas        1 mensagem
```

Cada caixa é uma camada independente. O `pipeline.py` só liga uma na outra.

## As camadas

```
radar/
  domain/        o centro: entidades e contratos. Não depende de nada.
  collectors/    de onde vêm as vagas          → cumpre ColetorDeVagas
  filtering/     regras baratas antes da IA
  matching/      IA: prompt, cliente, lotes    → cumpre AvaliadorDeVagas
  notification/  formatar e enviar a mensagem  → cumpre Notificador
  pipeline.py    orquestra; sem lógica própria
  __main__.py    linha de comando; monta as peças reais
  settings.py    variáveis de ambiente
```

### `domain/` — o que o sistema *é*

Três entidades (`Vaga`, `Perfil`, `ResultadoMatch`) e três contratos (`ColetorDeVagas`,
`AvaliadorDeVagas`, `Notificador`). Nada aqui sabe que Adzuna, Gemini ou Telegram existem.

A regra de dependência é uma só: **tudo aponta para o domínio; o domínio não aponta para
nada.** `collectors/` importa de `domain/`; `domain/` nunca importa de `collectors/`.

### Por que contratos (`Protocol`)?

O pipeline não pede "um `ColetorAdzuna`", pede "qualquer coisa com um método
`coletar() -> list[Vaga]`". Consequências práticas:

- **Trocar fonte** (Adzuna → Gupy): nova classe em `collectors/`, resto intocado.
- **Trocar IA** (Gemini → Claude): nova classe em `matching/`, resto intocado.
- **Testar o pipeline**: passa um coletor falso que devolve 3 vagas fixas. Zero rede,
  zero cota.

É isso que a proposta chama de "arquitetura limpa". Na prática significa: **a parte que
muda (infraestrutura) fica na borda; a parte que não muda (domínio) fica no centro.**

### `pipeline.py` — o maestro

```python
def executar(coletor, avaliador, notificador, perfil, quantidade, data):
    coletadas = coletor.coletar()
    candidatas = filtrar(coletadas, perfil)
    resultados = avaliador.avaliar(candidatas, perfil)
    selecionadas = ranquear(resultados)[:quantidade]
    notificador.enviar(formatar_mensagem(selecionadas, data))
```

Isso é literalmente o pipeline inteiro. Ele **recebe** as peças prontas (injeção de
dependência) em vez de criá-las. Quem cria as peças reais é o `__main__.py`; quem cria as
falsas são os testes.

## Decisões de arquitetura

### 1. Sem banco de dados na Fase 1

O GitHub Actions cria uma máquina nova a cada execução e a destrói no final. Não há onde
guardar um arquivo entre um dia e outro. Então:

- **SQLite foi descartado** — é um arquivo em disco, não sobreviveria.
- Versionar o `.db` no repositório: repositório público exporia `chat_id` dos usuários,
  e o job precisaria de permissão de escrita.
- `actions/cache`: não é durável, sofre evicção.

Na Fase 1 o filtro por data da Adzuna (últimos 2 dias) faz o papel de dedupe. Na Fase 2
entra **PostgreSQL no Supabase** — que a proposta já previa para o painel web, então adotar
agora evita migrar duas vezes. MySQL foi considerado e não oferece vantagem (JSON pior,
opções gratuitas piores).

### 2. Sem framework web

É um script disparado por cron, não um serviço HTTP. Flask/FastAPI seriam peso morto.
`httpx` para as duas chamadas HTTP (Adzuna e Telegram) basta.

### 3. Avaliadores com saída estruturada

- **Por que Gemini**: camada gratuita, suficiente para validar o produto.
- **Saída estruturada** (`response_schema` + Pydantic): a IA é obrigada a devolver JSON no
  formato `{id_vaga, nota, motivo, alerta_pegadinha}`. Sem parsing de texto livre, sem
  regex em cima de resposta de IA.
- **Temperatura 0**: mesma vaga, mesma nota. Importante para o usuário confiar no ranking.
- **Trocar de modelo** é uma variável de ambiente (`GEMINI_MODELO`). Trocar de provedor é
  um adapter novo em `matching/`.
- **Dois adapters** implementam a mesma interface: `AvaliadorGemini`, pela Developer API,
  e `AvaliadorAgy`, pelo Antigravity CLI local. `AVALIADOR=gemini_api|agy` escolhe qual usar.
- O adapter AGY roda em diretório temporário, com sandbox, timeout e JSON Schema; o fluxo do
  domínio recebe os mesmos `ResultadoMatch` em ambos os casos.

### 4. Pré-filtro por regras antes da IA

Regras baratas (regex) cortam o óbvio — "Desenvolvedor Sênior", "5 anos de experiência" —
antes de gastar cota e tempo de IA. A IA fica para o julgamento fino.

### 5. Avaliação em lotes com tolerância a falhas

O problema: a camada gratuita do Gemini permite ~20 requisições por **dia**. Uma chamada por
vaga estourava a cota em um único run.

A solução é em duas camadas, separadas de propósito:

```
AvaliadorEmLotes  (matching/lotes.py)   — sabe dividir, tentar de novo, desistir
      │  usa
      ▼
AvaliadorGemini/AvaliadorAgy            — sabem falar com seu mecanismo. Só isso.
```

O adapter selecionado recebe uma lista de vagas, faz **uma** chamada, devolve os resultados que
conseguiu casar por id. Não sabe o que é "tentar de novo".

`AvaliadorEmLotes` embrulha qualquer avaliador e aplica a estratégia:

| Situação | O que faz |
|---|---|
| 14 vagas, lote de 10 | 2 chamadas |
| lote de 10 falha (JSON quebrado, erro 500) | divide em 5 + 5, tenta cada; repete até isolar a vaga com problema |
| modelo esqueceu de responder 1 vaga | reavalia só ela |
| esqueceu mesmo sozinha | ignora e registra |
| cota excedida (HTTP 429) | para tudo, envia o que já tem |

Por que separar: a estratégia de resiliência não tem nada a ver com o mecanismo de IA.
`AvaliadorEmLotes` embrulha os dois adapters sem conhecer Gemini API ou AGY.

### 6. Formatar ≠ enviar

`formatador.py` é uma função pura: lista de resultados entra, texto sai. Testa sem rede.
`telegram.py` só faz o POST. O formato da mensagem já mudou três vezes; o envio, nenhuma.

### 7. Erros com nome

Cada camada tem sua exceção: `ErroDeColeta`, `ErroDeAvaliacao` (e a filha
`CotaDeAvaliacaoExcedida`), `ErroDeNotificacao`. Todas com mensagem limpa e **sem vazar
chave de API** no traceback (`raise ... from None`). O `__main__` captura as três e sai
com código 1 — o GitHub Actions fica vermelho e mostra o motivo em uma linha.

### 8. Configuração só por variável de ambiente

`Settings` (pydantic-settings) lê do `.env` local ou do ambiente do CI — o código não sabe a
diferença. Adzuna e Telegram são obrigatórios; `GEMINI_API_KEY` é condicional ao adapter.
O restante tem padrão. O `.env`
nunca é commitado; no GitHub as mesmas variáveis vêm dos secrets.

## Como cada ferramenta se encaixa

| Ferramenta | Papel | Por que essa |
|---|---|---|
| `uv` | Python + dependências + lock | rápido, instala o Python sozinho, `uv.lock` garante versões iguais em toda máquina |
| `ruff` | lint + formatação | uma ferramenta só, rápida, sem discussão de estilo |
| `pytest` + `pytest-httpx` | testes; simula HTTP | testar coletor e notificador sem rede |
| `pydantic` | entidades + validação do JSON da IA | nota fora de 0–100 nunca entra no sistema |
| `pydantic-settings` | `.env` → objeto tipado | erro claro quando falta variável |
| `httpx` | Adzuna e Telegram | simples, moderno, fácil de simular |
| `google-genai` | Gemini | SDK oficial com saída estruturada |
| GitHub Actions | cron diário | grátis em repo público, sem servidor |

## Regras do repositório

- Sem comentários no código; nomes autoexplicativos.
- Commits atômicos em [Conventional Commits](https://www.conventionalcommits.org), em
  português: `feat(matching): adiciona avaliador em lotes`.
- `.env` e segredos nunca commitados.
- Toda funcionalidade com teste; a suíte roda sem chave e sem internet.

## O que vem na Fase 2

Tudo abaixo entra **sem reescrever** o que existe — só adicionando na borda:

- **Banco (Supabase/PostgreSQL)**: `storage/` implementando um repositório definido em
  `domain/`. Histórico de vagas enviadas (dedupe real) e perfis dos usuários.
- **Vários usuários**: o pipeline roda uma vez e avalia por perfil; `chat_id` vem do banco,
  não do `.env`.
- **Cadastro pelo bot**: `python-telegram-bot` num processo separado; escreve o perfil no
  banco.
- **Mais fontes**: Gupy (API interna), Vagas.com/InfoJobs (scraping) — cada uma é uma classe
  em `collectors/` cumprindo `ColetorDeVagas`.
- **Cota da IA**: billing no Gemini (centavos por mês) ou `AvaliadorClaude` em `matching/`.
