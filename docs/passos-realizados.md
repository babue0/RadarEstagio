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
- `radar/domain/perfil_fixo.py`: o perfil usado quando não há banco. Nasceu com os dados reais do
  usuário nº 1 e passou a ser sintético em 04/09/2026, porque o repositório é público.

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
categoria `it-jobs` do Brasil, publicadas nos últimos `DIAS_RECENTES` dias (padrão atual 3; era 2),
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

## Passo 9 — Banco no Supabase e vários usuários (Fase 2)

**O que foi feito**

- `domain/`: entidade `Usuario` (id, perfil, `chat_id`) e contratos `RepositorioDeUsuarios`
  e `RepositorioDeAvaliacoes`; `Notificador.enviar` recebe o `chat_id`.
- `supabase/migrations/0001_tabelas_iniciais.sql`: `perfis` (com `token_vinculo` e
  `telegram_chat_id` já preparados para o webhook), `vagas`, `avaliacoes`, `envios`; RLS em
  todas, policy só em `perfis`.
- `storage/postgres.py` (`psycopg`, SQL puro, transação por usuário, erros viram
  `ErroDeArmazenamento`), `storage/memoria.py` (objeto nulo com o perfil fixo) e
  `storage/factory.py` (`abrir_repositorio`, decide por `DATABASE_URL`).
- `pipeline.py`: coleta e dedupe uma vez; por usuário, pré-filtra, tira o que ele já recebeu,
  avalia só o que não tem nota guardada, envia para o `chat_id` dele e grava. Erro no Telegram
  ou ao gravar de um usuário é aviso; os outros seguem.
- `DATABASE_URL` no `Settings` e no workflow; `TELEGRAM_CHAT_ID` só é obrigatório sem banco.

**Por quê**

É o pré-requisito de tudo da Fase 2: o site grava perfis, o webhook grava o `chat_id`, o job
lê os usuários. De quebra resolve duas dores do MVP: vaga não repete entre dias e a mesma
vaga não volta ao Gemini (cota).

**Como foi testado**

Testes unitários de pipeline (dois usuários, erro isolado, vaga já enviada, nota guardada,
falha ao gravar), memória e factory; `tests/test_storage_postgres.py` roda contra um Postgres
real quando `DATABASE_URL_TESTE` está definido e é pulado no CI. Sem `DATABASE_URL`, `verificar`
mostra "Banco: nenhum (perfil fixo)" e o comportamento é o mesmo do MVP.

Real, em 28/08/2026, com o projeto criado no Supabase e o perfil do usuário nº 1 inserido pelo
painel: `supabase db push --db-url` criou as 4 tabelas; primeira execução 51 coletadas → 48
únicas → 25 candidatas → 25 avaliadas → 5 enviadas, e o banco ficou com 25 vagas, 25
avaliações e 5 envios. Segunda execução logo depois: 20 candidatas (as 5 enviadas saíram),
20 com nota guardada, **0 chamadas à IA**, 5 enviadas.

---

## Passo 10 — Webhook do vínculo com o Telegram (Fase 2)

**O que foi feito**

- `supabase/functions/telegram-webhook/`: Edge Function em Deno. `index.ts` recebe o POST do
  Telegram, rejeita chamadas sem o header `X-Telegram-Bot-Api-Secret-Token` correto,
  atualiza `perfis.telegram_chat_id` onde `token_vinculo` bate e responde ao usuário no chat.
  `vinculo.ts` isola a regra pura (extrair token e `chat_id` da mensagem), coberta por
  `vinculo_test.ts` (`deno test`).
- `supabase/config.toml` com `verify_jwt = false` para essa função: quem chama é o Telegram,
  sem sessão do Supabase.
- Publicada com `supabase functions deploy`, segredos via `supabase secrets set` e webhook
  registrado com `setWebhook` (`secret_token`, `allowed_updates=["message"]`).

**Por quê**

Fecha o fluxo "criou conta → clicou no botão → recebe mensagem" sem digitar `chat_id` no
painel. Não depende do site: o link `t.me/RadarEstagio_bot?start=<token_vinculo>` funciona
com o token copiado da tabela.

**Como foi testado**

7 testes da regra pura. Real, em 28/08/2026: `telegram_chat_id` apagado no painel, link
aberto com o `token_vinculo`, bot respondeu "Telegram vinculado!" e `verificar` voltou a
mostrar 1 usuário ativo com Telegram vinculado. Descoberto no caminho que o username real do
bot é `RadarEstagio_bot`, corrigido nos docs.

---

## Passo 11 — Cadastro web e vínculo com o Telegram (Fase 2)

**O que foi feito**

- `web/`: o formulário deixou de ser uma demonstração em `localStorage` e passou a criar ou
  acessar uma conta pelo Supabase Auth, gravar o perfil diretamente na tabela `perfis` e abrir
  o deep link do bot com `token_vinculo`.
- Confirmação de e-mail suportada: os campos do perfil ficam temporariamente no navegador e o
  cadastro é retomado quando a sessão volta pelo link do Supabase. A senha nunca é armazenada
  pelo site.
- O estado final distingue perfil salvo, Telegram pendente e Radar ativado; ao voltar para a
  janela, o site consulta o perfil novamente para reconhecer o vínculo feito pelo webhook.
- `supabase/migrations/0002_permissoes_frontend.sql`: o usuário autenticado pode ler a própria
  linha e editar somente os campos do perfil. `token_vinculo` e `telegram_chat_id` continuam
  reservados ao banco e ao webhook.
- O frontend usa a chave publicável do projeto, apropriada para código cliente, e o projeto
  atual ficou registrado em `supabase/config.toml` e `web/config.js`.

**Como foi testado**

- A API de Auth do projeto atual respondeu com sucesso usando a chave publicável.
- As migrations `0001`, `0002` e `0003` foram aplicadas no projeto de produção
  `xrhvjwemmylwbqgluebc` (`sa-east-1`); a tabela `perfis` existe e
  uma consulta anônima é rejeitada.
- `tests/test_frontend_activation.py` verifica a ordem de carregamento, a presença do fluxo de
  Auth, a persistência em `perfis`, o deep link e a proteção dos campos de vínculo.
- Na verificação de 29/08/2026, 192 testes passaram e 4 testes de integração foram ignorados sem
  banco de teste configurado. Em 02/09/2026, a suíte tem 318 testes passando e 4 integrações
  ignoradas.

**Pendências operacionais**

- Trocar o Site URL do Supabase Auth de `http://localhost:3000` para
  `http://localhost:8000` e incluir essa URL na lista de redirects.
- ~~Publicar novamente a Edge Function e registrar o webhook do Telegram no projeto atual.~~
  Concluído em 29/08/2026 no projeto `xrhvjwemmylwbqgluebc`; a função ficou `ACTIVE` e o
  Telegram confirmou o destino sem erro recente.
- ~~Alinhar a `DATABASE_URL` do job com o banco do site e do webhook.~~ O secret já apontava
  para o projeto correto e o workflow manual de 29/08/2026 terminou com sucesso.
- O projeto `bnzogphdvpubtkcflcue` (`us-east-2`) foi criado por engano, não é usado pela
  aplicação e deve ser removido apenas depois de uma confirmação separada.

---

## Passo 12 — Ativação operacional e métricas (Fase 2)

**O que foi feito**

- Ativação operacional definida como a primeira entrega aceita pelo Telegram contendo ao menos
  uma recomendação. Cadastro, confirmação de e-mail, vínculo do Telegram e mensagem sem vagas não
  contam como ativação operacional. A ativação de produto começa na primeira abertura de vaga e
  ainda não é emitida.
- `perfis.ativado_em` registra o evento uma única vez. O pipeline atualiza o campo na mesma
  transação dos registros em `envios`, somente depois do envio bem-sucedido.
- A migration `0003_evento_ativacao.sql` cria o campo, retropreenche perfis com histórico e
  adiciona um índice parcial para consultas dos perfis com ativação operacional.
- `docs/metricas.md` documenta a taxa de ativação operacional em 7 dias, o tempo mediano até a
  primeira entrega e uma consulta de referência para a coorte madura dos últimos 30 dias.

**Como foi testado**

- O teste de integração verifica que uma entrega com vaga ativa operacionalmente o perfil, uma
  execução sem vaga não ativa e reprocessar a mesma entrega preserva o primeiro timestamp.
- A suíte local mantém os testes de PostgreSQL condicionados a `DATABASE_URL_TESTE`.
- A migration foi aplicada no projeto Supabase de produção `xrhvjwemmylwbqgluebc` em
  29/08/2026 e retropreencheu qualquer perfil que já tivesse histórico de envio.

---

## Passo 13 — Cobertura das fontes por cidade

**O que foi feito**

- Diagnóstico: a Adzuna marca a maioria das vagas brasileiras como categoria "Unknown". Com
  `category=it-jobs` a busca nacional devolvia 55 vagas em 5 dias; sem categoria e restrita
  ao Rio de Janeiro, 686. Para um perfil presencial no Rio, só 2 vagas chegavam ao Gemini.
- Adzuna: busca com `what_and=estágio` e `what_or` de termos de computação, sem categoria,
  até 4 páginas por região; uma busca nacional e uma por cidade (`where=`) de cada perfil
  presencial ou híbrido. A localização passou a usar `location.area` (cidade, estado), para
  que "Copacabana, Rio de Janeiro" conte como Rio de Janeiro.
- Gupy: em vez de oito termos no título, busca todos os estágios do país (até 10 páginas,
  ordenados por data) e todos os da cidade de cada perfil presencial ou híbrido (`city=`).
- `Perfil.nome_da_cidade()` extrai a cidade antes da vírgula; `cidades_de_interesse` reúne
  as cidades dos usuários ativos e a CLI as passa ao coletor (`rodar`, `coletar`, `avaliar`).
- Pré-filtro: `fora_da_area_de_tecnologia` agora descarta também título genérico sem sinal
  de computação na descrição, e a lista de outras áreas ganhou farmácia, turismo,
  treinamento e desenvolvimento, R&S, people, CRM, auditoria, comunicação e afins.

- Republicações: agregadores como Divulga Vagas e BuscarVagas publicam o mesmo anúncio com
  "empresa" diferente, e três cópias de "Estágio em Programação" entraram na mesma mensagem.
  `remover_republicacoes` une vagas de mesmo título (ignorando sufixo "- Vaga") e cidade cujas
  40 primeiras palavras da descrição coincidam em 80%; descrições curtas nunca são unidas.

**Como foi testado**

- Testes unitários para paginação, `where`/`city` por cidade, republicações, deduplicação entre a busca
  nacional e a da cidade, localização com bairro e as novas regras do pré-filtro.
- Coleta real em 30/08/2026 com os dois perfis presenciais no Rio: 703 vagas únicas
  (356 Adzuna, 347 Gupy), 210 no Rio, 55 candidatas após o pré-filtro (eram 2).

---

## Passo 14 — Instrumentação mínima do funil (Fase 2)

**O que foi feito**

- `0005_eventos_produto.sql` cria um catálogo fechado com os 16 eventos do plano RCD, contexto
  opcional de sessão, usuário, perfil e vaga, propriedades JSON limitadas e índices por jornada.
- A landing registra visualização, abertura do cadastro, conclusão das três etapas, salvamento
  do perfil e abertura do Telegram. Uma sessão anônima persistente permite reconstruir o trecho
  anterior à autenticação sem colocar dados do perfil na telemetria.
- Gatilhos registram os marcos autoritativos de conta, confirmação de e-mail, perfil, vínculo,
  primeira recomendação e pausa. Os dados existentes são retropreenchidos pela migration.
- RLS restringe visitantes e usuários autenticados aos eventos web esperados. Os eventos de
  vaga aberta, feedback e candidatura ficam reservados até as respectivas interações existirem.
- `docs/metricas.md` contém a matriz de emissores e uma consulta que reconstrói a primeira
  ocorrência de cada etapa por usuário, ligando sessões anônimas apenas quando a associação é
  inequívoca.

**Como foi testado**

- Testes estáticos verificam o catálogo, contexto, RLS, gatilhos, emissores web e identificação
  da posição dos CTAs.
- O teste de integração do repositório verifica que a primeira recomendação cria um único evento,
  mesmo quando o registro da entrega é repetido.

---

## Números atuais do MVP

- 14 passos documentados, seguidos por ajustes de matching e documentação.
- 322 testes coletados: 318 passam localmente e 4 integrações exigem um PostgreSQL de teste.
- 1 workflow configurado para disparo diário externo; as requisições ao Gemini variam conforme
  usuários e lotes.

## Pendências para o grupo decidir

- **Cota do Gemini para vários usuários**: medir chamadas e custo por usuário antes de ativar
  billing ou implementar outro adapter.
- **`.agents/skills`** no repositório público: manter ou remover.
