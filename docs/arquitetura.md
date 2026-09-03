# Arquitetura do Radar de Estágio

Como o sistema é organizado, por que foi organizado assim e quais decisões foram tomadas no
caminho. O histórico passo a passo está em [`passos-realizados.md`](passos-realizados.md).

## Em uma frase

Um script Python, disparado uma vez por dia pelo GitHub Actions, que coleta vagas, filtra,
avalia com IA e envia uma mensagem no Telegram para cada usuário — **sem servidor**; o banco
Supabase é acessado pelo job e pelo cadastro web.

## O fluxo

```
┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐
│  coletar   │ → │  dedupe    │ → │ pré-filtrar│ → │  avaliar   │ → │  ranquear  │ → │   enviar   │
│Adzuna+Gupy │   │título+emp. │   │  (regras)  │   │  (Gemini)  │   │  (top N)   │   │ (Telegram) │
└────────────┘   └────────────┘   └────────────┘   └────────────┘   └────────────┘   └────────────┘
   volume variável   volume variável  volume variável  lotes configuráveis  até N vagas   1+ mensagem
```

Cada caixa é uma camada independente. O `pipeline.py` só liga uma na outra. Com banco, as
três últimas caixas rodam uma vez por usuário, e o `storage/` entra antes de avaliar (o que
já tem nota e o que já foi enviado) e depois de enviar (grava vagas, notas e envios).

## As camadas

```
radar/
  domain/        o centro: entidades e contratos. Não depende de nada.
  collectors/    de onde vêm as vagas (um por fonte + composto) → cumpre ColetorDeVagas
  filtering/     dedupe e regras baratas antes da IA
  matching/      IA: prompt, cliente, lotes    → cumpre ExtratorDeVagas
                 pontuação determinística      → compatibilidade.py, avaliacoes.py
  notification/  formatar e enviar a mensagem  → cumpre Notificador
  storage/       usuários, notas e envios      → cumpre Repositorio (Postgres ou memória)
  pipeline.py    orquestra; sem lógica própria
  __main__.py    linha de comando; monta as peças reais
  settings.py    variáveis de ambiente
```

### `domain/` — o que o sistema *é*

Quatro entidades (`Vaga`, `Perfil`, `Usuario`, `ResultadoMatch`) e os contratos
(`ColetorDeVagas`, `ExtratorDeVagas`, `Notificador`, `RepositorioDeUsuarios`,
`RepositorioDeAvaliacoes`). Nada aqui sabe que Adzuna, Gemini ou Telegram existem.

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
def executar(coletor, extrator, notificador, repositorio, parametros, agora):
    unicas = remover_duplicatas(coletor.coletar())
    candidatas = candidatas_de_algum_perfil(unicas, usuarios)
    extracoes = obter_extracoes(extrator, repositorio, candidatas)  # uma vez, para todos
    for usuario in usuarios:  # por usuário, sem IA
        resultados = pontuar_vagas(filtrar(unicas, usuario.perfil), extracoes, usuario.perfil)
        notificador.enviar(usuario.chat_id, formatar_mensagem(ranquear(resultados), agora))
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

Na Fase 1 o filtro por data (`DIAS_RECENTES`) faz o papel de dedupe. Na Fase 2 entrou
**PostgreSQL no Supabase** — que a proposta já previa para o painel web, então adotar
agora evita migrar duas vezes. MySQL foi considerado e não oferece vantagem (JSON pior,
opções gratuitas piores). Ver a decisão 10.

### 2. Sem framework web

É um script disparado por cron, não um serviço HTTP. Flask/FastAPI seriam peso morto.
`httpx` para as duas chamadas HTTP (Adzuna e Telegram) basta.

### 3. Extração por vaga, pontuação por perfil

A IA extrai **fatos da vaga**; o Python **compara** esses fatos com cada perfil. A separação
existe por custo: o prompt não contém perfil algum, então uma vaga é extraída **uma vez** e a
extração serve todos os usuários. O custo de IA passou de O(usuários × vagas) para O(vagas), e
o vigésimo usuário não custa nada.

- **Por que Gemini**: camada gratuita, suficiente para validar o produto.
- **Saída estruturada** (`response_schema` + Pydantic): a IA devolve JSON no formato
  `{id_vaga, area_de_tecnologia, areas_da_vaga, cursos_aceitos, aceita_qualquer_curso,
  periodo_minimo, experiencia_minima_anos, experiencia_desejavel, habilidades_obrigatorias,
  habilidades_principais, habilidades_desejaveis, alerta_pegadinha}`. Tudo é fato do anúncio;
  nada depende de candidato.
- **A comparação é determinística** (`matching/compatibilidade.py`): `cursos_aceitos` vira
  compatível/parcial/incompatível contra um catálogo fechado de cursos de computação;
  `periodo_minimo` e `experiencia_minima_anos` viram o nível de período; os pontos a favor e
  contra são montados da comparação, não escritos pela IA. Mesmos dados, mesma nota, sempre.
- **Pontuação no Python** (`matching/avaliacoes.py`): habilidades valem 45 pontos, curso 10,
  área 10, período/experiência 15, logística 10 e áreas de interesse 10. A cobertura das
  habilidades é comparada por tecnologias normalizadas e exatas; `Java` não corresponde a
  `JavaScript`.
- **A extração fica em `vagas.extracao`** (JSONB). Reexecução no mesmo dia, usuário novo
  entrando ou coorte crescendo não gastam cota de novo.
- **Temperatura 0**: os mesmos dados tendem a produzir a mesma extração.
- **Trocar de modelo** é uma variável de ambiente (`GEMINI_MODELO`). Trocar de provedor é
  um adapter novo em `matching/`.
- **Dois adapters** implementam a mesma interface: `ExtratorGemini`, pela Developer API,
  e `ExtratorAgy`, pelo Antigravity CLI local. `AVALIADOR=gemini_api|agy` escolhe qual usar.
- O adapter AGY roda em diretório temporário, com sandbox, timeout e JSON Schema; o fluxo do
  domínio recebe as mesmas `ExtracaoDaVaga` em ambos os casos.

### 4. Pré-filtro por regras antes da IA

Regras baratas (regex) cortam o óbvio — "Desenvolvedor Sênior", "5 anos de experiência" —
antes de gastar cota e tempo de IA. A IA fica para o julgamento fino.

### 5. Extração em lotes com tolerância a falhas

O problema: a cota do Gemini varia por modelo e plano. Uma chamada por vaga multiplica custo,
latência e risco de limite, além de poder interromper uma execução com volume alto.

A solução é em duas camadas, separadas de propósito:

```
ExtratorEmLotes  (matching/lotes.py)   — sabe dividir, tentar de novo, desistir
      │  usa
      ▼
ExtratorGemini/ExtratorAgy             — sabem falar com seu mecanismo. Só isso.
```

O adapter selecionado recebe uma lista de vagas, faz **uma** chamada, devolve os resultados que
conseguiu casar por id. Não sabe o que é "tentar de novo".

`ExtratorEmLotes` embrulha qualquer extrator e aplica a estratégia:

| Situação | O que faz |
|---|---|
| 14 vagas, lote de 10 | 2 chamadas |
| lote de 10 falha (JSON quebrado, erro 500) | divide em 5 + 5, tenta cada; repete até isolar a vaga com problema |
| modelo esqueceu de responder 1 vaga | extrai só ela |
| esqueceu mesmo sozinha | ignora e registra |
| cota excedida (HTTP 429) | para tudo, envia o que já tem |

Por que separar: a estratégia de resiliência não tem nada a ver com o mecanismo de IA.
`ExtratorEmLotes` embrulha os dois adapters sem conhecer Gemini API ou AGY.

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

### 9. Várias fontes somadas, com dedupe sem banco

A Adzuna devolve descrição truncada e raramente informa modalidade; a Gupy tem API interna
(sem chave) com `workplaceType` estruturado e descrição completa. As duas são somadas por
`ColetorComposto` (`collectors/composto.py`), que cumpre `ColetorDeVagas` como qualquer
coletor: o pipeline não sabe quantas fontes existem. Uma fonte fora do ar vira `warning`; só
falha se nenhuma responder. `FONTES` liga e desliga fontes sem mexer no código.

A mesma vaga pode chegar pelas duas. `filtering/duplicatas.py` agrupa por título + empresa
normalizados e fica com a versão **mais completa**: quem informa modalidade ganha; empate →
descrição mais longa. Não precisa de IA para isso — é a mesma vaga, a nota seria a mesma; o
que muda é a informação que chega ao extrator.

`Vaga.modalidade` é opcional: a Gupy preenche, a Adzuna não. O pré-filtro decide pelo campo
quando existe e só recorre a regex no texto quando a fonte não informa.

### 10. Banco atrás de interface, com objeto nulo

O `pipeline.py` fala com um `Repositorio` (`domain/ports.py`) e nunca com o Postgres. Há
duas implementações em `storage/`: `RepositorioPostgres` (SQL puro com `psycopg`, sem ORM)
e `RepositorioEmMemoria`, que devolve o perfil fixo e não guarda nada. `abrir_repositorio`
escolhe pela presença de `DATABASE_URL`. O pipeline tem um único caminho: não existe
`if banco` em lugar nenhum fora da factory.

Regras para não afetar quem já usa:

- **Ler usuários é a única falha fatal.** Erro ao enviar para um usuário ou ao gravar depois
  do envio vira `warning` e o job segue para o próximo. Enviar é o produto; gravar é otimização.
- **Avaliação gravada antes do envio.** `guardar_avaliacoes` roda antes de chamar o Telegram e
  `registrar_envios` roda depois: uma falha de entrega não descarta o que a IA já custou, e o
  dia seguinte não reavalia as mesmas vagas.
- **Nada de mensagem vazia.** Sem vaga aprovada o job não envia nada. Depois de
  `DIAS_DE_SILENCIO_ATE_AVISAR` dias sem recomendação, e no máximo uma vez por período, sai um
  aviso de silêncio explicando que a busca continua. A notificação diária inútil era o caminho
  mais curto para o estudante bloquear o bot.
- **Falhas seguidas pausam o perfil.** Cada erro de envio incrementa `perfis.falhas_de_envio`;
  ao atingir `FALHAS_DE_ENVIO_ATE_PAUSAR` o perfil sai de `ativo`, emitindo `entregas_pausadas`.
  Um envio bem-sucedido zera a contagem. Sem isso, quem bloqueia o bot vira custo diário eterno.
- **Transação por operação**: as avaliações de um usuário entram juntas ou não entram, e o mesmo
  vale para os envios e a ativação.
- **Schema versionado** em `supabase/migrations/`, aplicado com `supabase db push`. É o
  contrato com o site: ninguém altera tabela pelo painel.
- **RLS** em todas as tabelas. Só `perfis` tem policy (cada usuário lê e edita a própria
  linha, para o site com a chave anônima); `eventos_produto` aceita apenas os eventos web
  permitidos para a sessão ou usuário atual. O job usa a string de conexão do Postgres, que
  ignora RLS, e ela só existe no `.env` e nos secrets.
- **Conexão pelo Session pooler** do Supabase: o runner do Actions só tem IPv4.
- **Toda execução se reporta.** Ao terminar, o job manda ao chat de operação
  (`TELEGRAM_CHAT_ID`) quantos usuários estavam ativos, quantos receberam recomendação, quantas
  vagas saíram e quantas requisições o extrator consumiu. Um erro conhecido vira aviso de falha
  antes de derrubar o processo; um kill por timeout, que o Python não consegue reportar, é
  coberto pelo passo `if: failure()` do workflow, que manda o link do run. O disparo é externo
  (cron-job.org): sem esse retorno, dois dias parados passam despercebidos, como já aconteceu.

### 11. Eventos de produto com fonte autoritativa

`eventos_produto` concentra o funil em um catálogo fechado. A landing registra visita, CTA,
etapas e abertura do Telegram com um UUID de sessão sem dados pessoais. Gatilhos do Postgres
registram conta criada, confirmação de e-mail, perfil salvo, Telegram vinculado, primeira
recomendação e pausa, porque esses marcos não devem depender do navegador permanecer aberto.

A sessão anônima é ligada ao usuário por um evento autenticado de `perfil_salvo`. Consultas usam
a primeira ocorrência de cada nome, pois o gatilho autoritativo e o navegador podem registrar o
mesmo marco. Os eventos de clique, utilidade e candidatura permanecem reservados até existirem
interações reais no Telegram; o contrato não fabrica comportamento futuro.

## Como cada ferramenta se encaixa

| Ferramenta | Papel | Por que essa |
|---|---|---|
| `uv` | Python + dependências + lock | rápido, instala o Python sozinho, `uv.lock` garante versões iguais em toda máquina |
| `ruff` | lint + formatação | uma ferramenta só, rápida, sem discussão de estilo |
| `pytest` + `pytest-httpx` | testes; simula HTTP | testar coletor e notificador sem rede |
| `pydantic` | entidades + validação do JSON da IA | fatores inválidos não entram no cálculo da nota |
| `pydantic-settings` | `.env` → objeto tipado | erro claro quando falta variável |
| `httpx` | Adzuna e Telegram | simples, moderno, fácil de simular |
| `google-genai` | Gemini | SDK oficial com saída estruturada |
| GitHub Actions | executa o workflow manual | repositório público, sem servidor dedicado |
| cron-job.org | dispara o workflow diariamente | substitui o `schedule` nativo que falhou em testes |

## Regras do repositório

- Sem comentários no código; nomes autoexplicativos.
- Commits atômicos em [Conventional Commits](https://www.conventionalcommits.org), em
  português: `feat(matching): adiciona extrator em lotes`.
- `.env` e segredos nunca commitados.
- Toda funcionalidade com teste; a suíte roda sem chave e sem internet.

## Custo de IA por usuário

A extração compartilhada é o que torna a coorte do piloto viável na cota gratuita. Antes, cada
perfil reavaliava as mesmas vagas: 20 estudantes no primeiro dia pediam cerca de 120 requisições
contra um limite de 20 por minuto, e o job morria no timeout antes de atender a fila inteira —
sempre pelos usuários mais recentes, porque a fila é ordenada por `criado_em`.

Agora o número de requisições depende só de quantas vagas novas passaram no pré-filtro de algum
perfil. O resumo de cada execução (decisão 10) informa esse número, e o teste
`test_dobrar_os_usuarios_nao_dobra_as_vagas_extraidas` impede que a propriedade se perca.

## Estado da Fase 2

A base da Fase 2 já está integrada ao sistema. O que ainda não foi implementado permanece como
trabalho futuro:

- ~~**Banco (Supabase/PostgreSQL)** e **vários usuários**~~ — feito (Passo 9, decisão 10).
- ~~**Cadastro no site**~~ — feito (Passo 11). A landing estática usa Supabase Auth,
  grava o perfil diretamente sob RLS, retoma o cadastro após a confirmação de e-mail e
  termina no deep link do Telegram. O contrato entre as partes continua sendo o schema do
  banco, não uma API do `radar/`.
- ~~**Vínculo com o Telegram**~~ — feito (Passo 10). O site abre
  `t.me/RadarEstagio_bot?start=<token>` com o `token_vinculo` do usuário; o Telegram chama a
  Edge Function `supabase/functions/telegram-webhook/`, que confere o segredo do webhook,
  troca o token pelo `chat_id` e grava no perfil. A função fica fora do `radar/` (Deno é a
  plataforma das Edge Functions) e só tem uma regra pura testada (`vinculo.ts`). O bot
  continua só enviando mensagens; nada de `python-telegram-bot` nem processo escutando.
- **Mais fontes**: só depois de a validação comprovar cobertura insuficiente. Cada nova fonte deve
  cumprir `ColetorDeVagas` e ser registrada na factory e em `FONTES`.
- **Cota da IA**: medir chamadas e custo por usuário com ativação operacional antes de contratar
  capacidade ou implementar outro adapter em `matching/`.
