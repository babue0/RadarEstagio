# O que foi feito em cada passo

Registro do MVP (Fase 1), passo a passo, seguindo o [plano](plano-mvp.md). Para cada passo:
o que foi construído, por que daquele jeito, como foi testado e o que aprendemos no caminho.

Leia junto com [`arquitetura.md`](arquitetura.md), que explica como as peças se encaixam.

---

## Passo 0 — Fundação

**O que foi feito**

- Projeto Python gerenciado pelo `uv` (`pyproject.toml`, `uv.lock`). Não precisa instalar
  Python à parte: o `uv` baixa a versão certa.
- `ruff` para lint e formatação, `pytest` para testes.
- `radar/settings.py`: classe `Settings` que lê as variáveis de ambiente (do `.env` local ou
  do ambiente do GitHub Actions). Variável obrigatória vazia ou ausente é rejeitada na hora,
  com a lista do que falta.
- `.env.example` com os nomes das variáveis; `.gitignore` bloqueando `.env`, `.venv`, caches.

**Por quê**

Sem isso cada máquina teria um ambiente diferente. O `uv.lock` garante que todo mundo — e o
GitHub — instala exatamente as mesmas versões.

**Como foi testado**

`uv run python -m radar verificar` imprime a configuração carregada ou lista as variáveis
faltantes.

---

## Passo 1 — Domínio

**O que foi feito**

- `radar/domain/models.py`: as três entidades do sistema.
  - `Vaga` — o que vem da fonte: id, título, empresa, localização, descrição, url, data.
  - `Perfil` — curso, período, habilidades, cidade, modalidade (remoto/presencial/híbrido).
  - `ResultadoMatch` — uma vaga + nota (0–100) + pontos a favor e contra + alerta de pegadinha opcional.
- `radar/domain/ports.py`: os **contratos** (`Protocol`) que as outras camadas cumprem:
  `ColetorDeVagas`, `AvaliadorDeVagas`, `Notificador`.
- `radar/domain/perfil_fixo.py`: o perfil do usuário nº 1 (Engenharia de Software, 4º
  período, Python/Git/JavaScript/React/SQL/Java, Rio de Janeiro, remoto).

**Por quê**

O domínio é o centro do sistema e não depende de nada externo — nem de Adzuna, nem de Gemini,
nem de Telegram. Isso permite trocar qualquer fonte, IA ou canal sem tocar aqui.

Perfil fixo porque a Fase 1 tem um único usuário. Cadastro pelo site é Fase 2.

**Como foi testado**

`tests/test_models.py`: validações do Pydantic (nota fora de 0–100 é rejeitada, perfil sem
habilidade é rejeitado etc.).

---

## Passo 2 — Coleta na Adzuna

**O que foi feito**

`radar/collectors/adzuna.py`: `ColetorAdzuna` chama a API oficial buscando `estágio` na
categoria `it-jobs` do Brasil, publicadas nos últimos `DIAS_RECENTES` dias (padrão 2),
50 por página. Converte cada item da resposta em `Vaga`. Erros HTTP e de rede viram
`ErroDeColeta` com mensagem limpa — sem vazar a chave da API no traceback.

**Por quê**

Adzuna tem API oficial e gratuita; scraping (Gupy, Vagas.com) fica para depois. O filtro por
data faz o papel de "dedupe" na Fase 1: só chegam vagas novas.

**Como foi testado**

- `tests/test_adzuna.py` com uma resposta real gravada em `tests/fixtures/` e `pytest-httpx`
  simulando a rede: conversão dos campos, parâmetros enviados, erros 401/500/timeout.
- Manual: `uv run python -m radar coletar` lista as vagas reais.

---

## Passo 3 — Pré-filtro por regras

**O que foi feito**

`radar/filtering/prefiltro.py`: antes de gastar IA, descarta por regras simples:

- não menciona estágio no título;
- título pede pleno/sênior/especialista/coordenador;
- descrição exige 2 a 9 anos de experiência;
- (só se o perfil for presencial) vaga fora da cidade do perfil. Antes havia uma exceção para
  texto com "remoto"/"home office", mas ela deixava passar vagas de SP cuja descrição dizia
  "suporte técnico presencial e remoto"; perfil presencial agora só recebe vagas da sua cidade.
  A comparação usa só a cidade (antes da vírgula): "Campinas, São Paulo" não é São Paulo.

Texto é normalizado (sem acento, minúsculas) antes de comparar.

**Por quê**

Cada chamada à IA custa cota e tempo. Regras baratas cortam o lixo óbvio primeiro.

**Como foi testado**

`tests/test_prefiltro.py`, 32 casos cobrindo cada regra com e sem acento, maiúsculas,
variações em inglês.

---

## Passo 4 — Avaliação com Gemini

**O que foi feito**

- `radar/matching/prompt.py`: monta o texto enviado à IA — instruções de "recrutador",
  perfil do candidato e a(s) vaga(s).
- `radar/matching/gemini.py`: `AvaliadorGemini` chama o Gemini pedindo **saída estruturada**
  (JSON validado por um schema Pydantic), com temperatura 0 para respostas estáveis.
  Erros da API viram `ErroDeAvaliacao`; JSON fora do esperado também.

**Por quê**

Saída estruturada elimina o parsing frágil de texto livre: ou vem um JSON válido no formato
`{nota, pontos_a_favor, pontos_contra, alerta_pegadinha}` ou é erro (na época, um único campo `motivo` em frase). Temperatura 0 faz a mesma vaga receber a mesma
nota em dias diferentes.

**O que aprendemos**

- `gemini-2.5-flash` foi recusado pela API para contas novas → padrão passou a ser
  `gemini-3.6-flash` (configurável por `GEMINI_MODELO`).
- Cada chamada leva ~5 s, a maior parte em "thinking" do modelo.

**Como foi testado**

- `tests/test_gemini.py` com um cliente falso: conversão do JSON, schema enviado, respostas
  inválidas, erros de API.
- Manual: `uv run python -m radar avaliar` com 3 vagas reais — notas coerentes (30/10/40 para
  vagas em outras cidades ou fora da área).

---

## Passo 5 — Mensagem e envio no Telegram

**O que foi feito**

- `radar/notification/formatador.py`: transforma a lista de `ResultadoMatch` em texto HTML
  do Telegram — cabeçalho com data, vagas ordenadas por nota com título, empresa, nota,
  pontos a favor/contra, alerta (só se houver) e link; separador `───` entre vagas; "nenhuma vaga hoje"
  quando a lista está vazia. Caracteres `<`, `>`, `&` são escapados. Mensagem acima de
  4096 caracteres (limite do Telegram) é dividida **sem cortar uma vaga no meio**.
- `radar/notification/telegram.py`: `NotificadorTelegram` faz um POST em
  `api.telegram.org/bot<token>/sendMessage`. Erros viram `ErroDeNotificacao` com a descrição
  do Telegram (ex.: "chat not found").

**Por quê**

Formatar e enviar são separados de propósito: o formato da mensagem muda toda hora; o envio
nunca muda. E o formatador é uma função pura — testa sem internet.

**Como foi testado**

- `tests/test_formatador.py` e `tests/test_telegram.py` (rede simulada).
- Manual: `uv run python -m radar testar-telegram` envia "Radar OK".

---

## Passo 6 — Pipeline

**O que foi feito**

- `radar/pipeline.py`: `executar(coletor, avaliador, notificador, perfil, quantidade, data)`
  — coleta → pré-filtra → avalia → ranqueia → corta nas top N → formata → envia. Recebe as
  peças de fora, não cria nenhuma.
- `radar/__main__.py`: `uv run python -m radar` (comando `rodar`) monta as peças reais e
  chama o pipeline. Os comandos de teste dos passos anteriores continuam disponíveis.

**Por quê**

O pipeline receber as peças de fora é o que permite testá-lo com coletor/avaliador/
notificador falsos, sem gastar nenhuma cota.

**O que aprendemos — a cota do Gemini**

O primeiro run real revelou: a camada gratuita do `gemini-3.6-flash` permite ~**20
requisições por dia**. Com uma chamada por vaga, um único run com 14 vagas quase esgotava
a cota, e os testes do dia já a tinham consumido.

Tentamos esperar 30 s e repetir: inútil, o limite é diário, não por minuto (13 minutos de
espera sem nenhuma resposta). A solução veio em duas partes:

1. Ao receber HTTP 429, o avaliador levanta `CotaDeAvaliacaoExcedida` e o sistema **para de
   avaliar na hora** e envia o que já tem, em vez de bater 14 vezes na mesma parede.
2. **Avaliação em lotes** (ver abaixo).

**Como foi testado**

- `tests/test_pipeline.py` com peças falsas: ordem por nota, corte em N, pré-filtro aplicado,
  vaga sem resultado fica fora, lista vazia manda a mensagem certa.
- Manual: `uv run python -m radar` → mensagem real com 5 vagas avaliadas no Telegram.

---

## Melhoria — Avaliação em lotes

Feita depois do Passo 6, por causa da cota.

**O que foi feito**

- O contrato `AvaliadorDeVagas.avaliar` passou a receber uma **lista** de vagas e devolver
  uma lista de resultados (mudança incompatível, marcada com `!` no commit).
- `AvaliadorGemini` manda até `GEMINI_VAGAS_POR_LOTE` vagas (padrão 10) em **uma** chamada;
  o JSON de resposta tem um item por vaga, casado pelo `id_vaga`. Ids inventados ou
  repetidos são ignorados.
- `radar/matching/lotes.py`: `AvaliadorEmLotes` embrulha qualquer avaliador e cuida da
  resiliência:
  - divide as vagas em lotes;
  - um lote que falha é **dividido ao meio** e cada metade tentada de novo, até isolar a
    vaga problemática — só ela é perdida;
  - vaga que o modelo esqueceu de responder é reavaliada sozinha;
  - cota excedida → para e devolve o que já tem (sem dividir, não adiantaria).

**Resultado**

14 vagas = 2 requisições em vez de 14. A cota diária passou a aguentar ~7 runs.

**Como foi testado**

`tests/test_lotes.py` cobre cada cenário acima com um avaliador falso programável.

---

## Melhoria — Mensagem mais curta

O primeiro print real mostrou motivos em parágrafo e alerta repetindo o motivo ("é em São
Paulo" aparecia duas vezes). Mudanças no prompt: motivo com no máximo 15 palavras, alerta
com no máximo 10, e alerta restrito a problemas que o título esconde (exige pleno, comercial
disfarçado de TI, sem remuneração) — localização e modalidade ficam só no motivo.

Confirmado no run seguinte: cada vaga em 1 linha de motivo, alerta só onde havia pegadinha
de verdade.

---

## Melhoria — Pontos a favor e contra no lugar do motivo

Com 15 palavras o motivo ficou vago ("cumpre 1 requisito da área de TI"). A frase foi
substituída por duas listas de até 3 itens concretos (`pontos_a_favor`, `pontos_contra`),
cada item com no máximo 4 palavras. A mensagem mostra `✅ Python · SQL · Remoto` e
`❌ Exige Docker`. Mesmo tamanho, muito mais informação, e a proporção de ✅/❌ explica a
nota visualmente.

---

## Melhoria — Modalidade respeitada

Um run real listou 4 vagas em outras cidades para um perfil remoto, com nota até 85. Duas
causas: o pré-filtro só avaliava localização para perfil **presencial**, e a IA deduzia
"presencial" pela cidade em vagas que não informavam a modalidade.

- `prefiltro.py`: para perfil remoto, vaga que menciona presencial/híbrido sem citar remoto
  é descartada; vaga remota passa de qualquer cidade; vaga sem modalidade passa.
- Prompt: proibido deduzir modalidade pela cidade; sem modalidade → "Modalidade não
  informada" nos pontos contra e ~10 pontos a menos; remota → cidade não é ponto contra;
  explicitamente presencial → nota máxima 30.

---

## Passo 7 — Execução diária no GitHub Actions

**O que foi feito**

`.github/workflows/radar-diario.yml`: quando disparado (cron externo às 07:23 Brasília ou
botão *Run workflow*), o GitHub liga uma máquina, baixa o código, instala o `uv` e as
dependências travadas no `uv.lock`, e roda `uv run python -m radar`. As chaves vêm dos
secrets do repositório, com os mesmos nomes do `.env`.

**Por quê**

Sem servidor próprio e de graça para repositório público. É também o motivo de não existir
banco na Fase 1: a máquina é destruída ao final de cada execução.

**Como foi testado**

Disparo manual pelo site → job verde → mensagem com vagas reais chegou no Telegram vinda
da máquina do GitHub.

**O que aprendemos — o cron não é garantido**

No primeiro dia agendado (`0 11 * * *`, 08:00) o GitHub simplesmente não disparou o run:
a API do repositório mostrava apenas o disparo manual. Não foi erro de código nem de chave —
o `schedule` do GitHub Actions é "melhor esforço", e o minuto `:00` de hora cheia é o horário
mais congestionado. Por isso o cron passou para `23 10 * * *` (07:23 em Brasília), fora do
topo da hora. No segundo dia, às 07:23, também não disparou: 0 runs com evento `schedule`
em dois dias, sem incidente aberto no GitHub. Solução adotada: o `schedule` saiu do workflow
e um job no cron-job.org (fuso America/Sao_Paulo, `23 7 * * *`) faz `POST` em
`/repos/babue0/RadarEstagio/actions/workflows/radar-diario.yml/dispatches` com body
`{"ref":"main"}` e um fine-grained token (Actions: Read and write). O `workflow_dispatch`
disparou na hora em todos os testes.

O primeiro disparo externo revelou outro bug: a Gupy devolve alguns itens com `publishedDate`
só com a data (`"2026-08-27"`), sem fuso, e a comparação com a data-limite em UTC levantava
`TypeError`. Corrigido em `collectors/gupy.py` tratando data sem fuso como UTC.

---

## Melhoria — Gupy, múltiplas fontes e dedupe

**O que foi feito**

- `Vaga.modalidade` opcional (`domain/models.py`). O pré-filtro decide por ela quando a fonte
  informa e só usa regex no texto quando não; o prompt mostra a modalidade à IA.
- `collectors/gupy.py`: `ColetorGupy` usa a API interna do portal
  (`employability-portal.gupy.io/api/v1/jobs`, sem chave), busca estágios por termos de
  tecnologia, pagina até `DIAS_RECENTES`, une por id, limpa o HTML da descrição e mapeia
  `workplaceType` → `Modalidade`.
- `collectors/composto.py`: `ColetorComposto` soma as fontes; uma fora do ar vira aviso e só
  falha se nenhuma responder.
- `filtering/duplicatas.py`: `remover_duplicatas` agrupa por título + empresa normalizados.
- `FONTES` (padrão `adzuna,gupy`) e `DIAS_RECENTES` (antiga `ADZUNA_DIAS_RECENTES`);
  `collectors/factory.py` monta o composto a partir de `FONTES`.

**Por quê**

A Adzuna raramente informa modalidade, e a IA acabava escrevendo "Modalidade não informada" em
quase toda vaga. A Gupy resolve isso de forma estruturada e traz vagas que a Adzuna não tem.

**Como escolher entre duplicatas**

É a mesma vaga, então a nota seria a mesma — não faz sentido gastar IA. Fica a versão mais
completa: quem informa modalidade ganha; empate → descrição mais longa. Na prática a Gupy vence
quando a vaga está nas duas.

**Como foi testado**

Testes unitários com fixture real da Gupy (`tests/fixtures/gupy_resposta.json`), paginação,
corte por data, união entre termos, composto com fonte falhando, dedupe. `coletar` real:
27 Adzuna + 9 Gupy → 34 únicas, todas as da Gupy com modalidade.

---

## Passo 8 — README

`README.md` para quem clona o projeto do zero: instalação na ordem, onde pegar cada chave,
como criar o bot no Telegram e descobrir o `chat_id`, estrutura do `.env`, comandos e onde
disparar o workflow no GitHub.

---

## Números finais do MVP

- 9 passos, ~40 commits atômicos em Conventional Commits.
- 165 testes automatizados, nenhum precisa de chave ou internet.
- 1 execução diária automática; 2 requisições ao Gemini por execução.

## Pendências para o grupo decidir

- **Nota mínima** para uma vaga entrar na mensagem (hoje entram as 5 melhores mesmo com
  nota 25).
- **Cota do Gemini para vários usuários**: ativar billing (centavos/mês) ou migrar para
  Claude Haiku (novo `AvaliadorClaude` em `matching/`, sem tocar no resto).
- **`.agents/skills`** no repositório público: manter ou remover.
