# Auditoria RCD e plano de execução

**Data:** 03/09/2026

**Escopo auditado:** `radar/`, `web/`, `supabase/migrations/`, `supabase/functions/`,
`.github/workflows/`, `docs/metricas.md` e `docs/plano-melhorias-rcd.md`.

**Framework:** Revenue-Centric Design, na ordem
_corrigir → medir → ativar → reter → provar → monetizar → diferenciar_.

Este documento não substitui [`plano-melhorias-rcd.md`](plano-melhorias-rcd.md), que continua
sendo a estratégia. Ele audita o que existe hoje no código, corrige o backlog priorizado à luz
do que foi encontrado e define o que fazer nas próximas seis semanas.

## 1. Veredito

A base técnica está saudável: 318 testes passam, o lint está limpo, as camadas são respeitadas e
a pontuação é determinística e justificada. O que impede o piloto não é qualidade de código.

São três coisas:

1. **O custo de IA cresce com o número de usuários**, e o piloto de 10–20 estudantes não cabe na
   cota gratuita nem no timeout do job.
2. **A North Star declarada é incomputável hoje** — nenhum evento de valor é emitido. O que se
   mede é entrega, não utilidade.
3. **O tempo até a primeira entrega ainda é "amanhã de manhã"**, contra a meta de 15 minutos, e o
   onboarding termina sem o estudante ver uma única vaga.

Rodar o piloto antes de resolver esses três pontos produz depoimentos, não dados — e queima a
única coorte de estudantes disponível.

## 2. Achados

### A. Bloqueadores do piloto

#### A1 — O custo de IA é O(usuários × vagas) e o piloto estoura a cota

`pipeline.py:73` chama `avaliador.avaliar(pendentes, usuario.perfil)` dentro do laço de usuários.
As vagas são coletadas uma vez, mas avaliadas uma vez **por perfil**.

Com as ~55 candidatas por dia medidas para o perfil Rio/presencial e lotes de 10
(`GEMINI_VAGAS_POR_LOTE`), o primeiro dia de cada usuário custa cerca de 6 requisições. Vinte
usuários entrando na mesma semana pedem cerca de 120 requisições contra uma cota gratuita de
20 por minuto.

`AvaliadorEmLotes` não distribui as chamadas: ele estoura, lê o `retry in Ns`, espera cerca de
60 s, tenta 3 vezes e desiste devolvendo o resultado parcial (`matching/lotes.py:37-60`). Com
`timeout-minutes: 15` no workflow (`.github/workflows/radar-diario.yml:8`), o job é morto no meio
da fila.

**Agravante:** `SQL_USUARIOS_ATIVOS` ordena por `criado_em` (`storage/postgres.py:12-18`). Quem
entrou por último é sistematicamente quem fica sem mensagem — exatamente o usuário cuja ativação
se quer medir. A falha é silenciosa: nenhum erro, apenas ausência.

#### A2 — Falha do Telegram descarta avaliações já pagas

`atender_usuario` retorna antes de `repositorio.registrar` quando o envio falha
(`pipeline.py:90-96`). Se o estudante bloqueou o bot ou a rede oscilou, as avaliações do dia são
jogadas fora e refeitas amanhã, indefinidamente, porque nada marca o usuário como inalcançável.
Um único usuário que bloqueia o bot vira um custo diário permanente.

#### A3 — Nenhum alarme quando o job não roda

O workflow só tem `workflow_dispatch` e quem dispara é um job externo no cron-job.org. Nada avisa
se ele parar — foi assim que o `schedule` nativo ficou 2 dias fora do ar. Em um piloto de duas
semanas, dois dias de silêncio não observado invalidam a coorte.

### B. A métrica que importa não é mensurável

#### B1 — Nenhum evento de valor é emitido

`vaga_aberta`, `vaga_util`, `vaga_irrelevante` e `candidatura_iniciada` existem no catálogo
(`0005_eventos_produto.sql`) mas não têm emissor. Consequência direta: **North Star, tempo até o
valor, retenção D7 e o resultado final de negócio são todos incomputáveis hoje.**

#### B2 — A telemetria web falha em silêncio

`registerEvent` engole qualquer erro (`web/assets/app.js:57-66`) e todos os chamadores usam
`void registerEvent(...)`. Se a chave pública mudar, a RLS bloquear ou o insert quebrar, o funil
fica vazio e ninguém percebe até tentar analisar a coorte — depois do piloto, quando não há mais
como refazer.

#### B3 — `landing_visualizada` conta recarregamentos

O evento é emitido a cada carregamento (`app.js:519`), sem deduplicação por sessão. A taxa
landing → cadastro fica diluída justamente no topo do funil que vai orientar a escolha de canal.

### C. Ativação

#### C1 — Não existe busca imediata após o vínculo

O único gatilho é o job diário. Meta do plano: mediana abaixo de 15 minutos. Realidade: até 24
horas, com probabilidade zero de atingir a meta. É o P0 mais antigo em aberto.

#### C2 — O onboarding termina sem prova de valor

`showActivation` encerra com "O Radar enviará as oportunidades compatíveis nas próximas
execuções" (`app.js:309`). O estudante fecha a aba sem ter visto uma vaga. É o ponto de maior
evasão possível e não há nada medindo isso além da ausência posterior.

#### C3 — Mensagem vazia todo dia

`atender_usuario` chama `notificador.enviar` incondicionalmente; sem vagas aprovadas o estudante
recebe "Nenhuma vaga compatível com o seu perfil hoje." diariamente (`notification/formatador.py:19`).
Para perfis presenciais em cidades menores isso é uma notificação inútil por dia — o caminho mais
curto para bloquear o bot, o que por sua vez dispara A2.

### D. Retenção, controle e conformidade

#### D1 — Sem editar, pausar ou retomar

Os grants já permitem escrever `ativo` e os campos do perfil (`0002`, `0004`, `0006`) e o
repositório já filtra `where ativo`. Falta apenas a interface. Sem pausa, a única saída é
bloquear o bot — e o sinal de churn se perde.

#### D2 — Sem exclusão de dados e sem aviso de privacidade

Nenhum caminho de exclusão de conta e dados, nenhum texto de finalidade. Produto público, dados
de estudantes reais, repositório público. Isso bloqueia a divulgação em turmas e coordenações,
que são dois dos três canais escolhidos na estratégia de distribuição.

#### D3 — `token_vinculo` é permanente e reutilizável

A Edge Function faz `update ... eq("token_vinculo", token)` sem invalidar nada
(`supabase/functions/telegram-webhook/index.ts:28-36`). Quem obtiver o link
`t.me/RadarEstagio_bot?start=<uuid>` — print compartilhado, histórico do Telegram, celular
emprestado — vincula o próprio chat e passa a receber as vagas daquele perfil. Como
`telegram_chat_id` é `unique`, o dono legítimo fica sem conseguir se revincular. Está no plano
como P1 desde o início e o custo de corrigir é baixo.

### E. Dívida silenciosa

#### E1 — `cidades_aceitas` e `modalidades_aceitas` são schema morto

A migration `0004_preferencias_multiplas.sql` criou as colunas, deu grant e retropreencheu os
dados. Nenhum código as lê ou escreve: `profileFromForm` envia apenas `cidade` e `modalidade`
(`app.js:233-247`) e `SQL_USUARIOS_ATIVOS` seleciona apenas as colunas singulares. É uma armadilha
para o item D1: a tela de edição vai gravar `cidade` e deixar `cidades_aceitas` mentindo.

#### E2 — Dados pessoais versionados

`domain/perfil_fixo.py` contém curso, período, habilidades e cidade reais do usuário nº 1 em um
repositório público.

## 3. A decisão pendente sobre a cota do Gemini

A pendência registrada em `passos-realizados.md` ("medir chamadas e custo por usuário antes de
ativar billing") tem uma resposta melhor que billing: **separar extração de pontuação**.

Olhando `AvaliacaoIA` (`matching/avaliacoes.py:77-87`), a maior parte do que a IA devolve é fato
da vaga, não do perfil:

| Campo | Depende do perfil? |
| --- | --- |
| `habilidades_obrigatorias`, `habilidades_principais`, `habilidades_desejaveis` | não |
| `areas_da_vaga` | não |
| `alerta_pegadinha` | não |
| `area`, `curso`, `periodo_experiencia` | sim, mas é comparação, não julgamento |
| `pontos_a_favor`, `pontos_contra` | sim, e já são reescritos pelo código |

A pontuação já é inteiramente determinística: `_calcular_nota` apenas combina coeficientes
(`avaliacoes.py:124-138`), e `_compatibilidade_logistica` já resolve localização e modalidade sem
IA nenhuma.

Se o prompt passar a extrair também **cursos aceitos, período mínimo e experiência exigida** como
fatos da vaga, os três níveis restantes viram comparação determinística com o perfil, e os pontos
a favor e contra passam a ser gerados a partir dessa comparação — como `_avisos_objetivos` já faz.

Resultado: **uma chamada de IA por vaga, reaproveitada por todos os usuários.** O custo passa de
O(usuários × vagas) para O(vagas), e o vigésimo usuário custa zero. A cota gratuita deixa de ser
um limite de crescimento e billing deixa de ser necessário para o piloto.

Só devem ser extraídas as vagas que passam no pré-filtro de pelo menos um perfil, não todas as
coletadas.

## 4. Backlog revisado

| # | Entrega | Achado | Sprint |
| --- | --- | --- | --- |
| 1 | Extração por vaga, pontuação por perfil | A1 | 0 |
| 2 | Gravar avaliações antes de enviar; marcar usuário inalcançável | A2 | 0 |
| 3 | Aviso de execução e de falha do job | A3 | 0 |
| 4 | Não enviar mensagem vazia diária | C3 | 0 |
| 5 | Telemetria web que falha visível | B2, B3 | 0 |
| 6 | Link rastreável e evento `vaga_aberta` | B1 | 1 |
| 7 | Feedback e candidatura por botões no Telegram | B1 | 1 |
| 8 | Consulta de funil de valor e custo por usuário | B1 | 1 |
| 9 | Primeira busca imediata após o vínculo | C1 | 2 |
| 10 | Primeira recomendação visível no onboarding | C2 | 2 |
| 11 | Página de perfil: editar, pausar, desvincular, excluir | D1, D2 | 3 |
| 12 | Token de vínculo de uso único | D3 | 3 |
| 13 | Aviso de privacidade e exclusão sem contato | D2 | 3 |
| 14 | Resolver `cidades_aceitas`/`modalidades_aceitas` | E1 | 3 |
| 15 | Remover dados pessoais do `perfil_fixo` | E2 | 3 |
| 16 | Piloto com 10–20 estudantes e 5 entrevistas | — | 4 |
| 17 | Landing baseada em prova | — | 4 |
| 18 | Teste de transação com os dez primeiros | — | 5 |

## 5. Plano de execução

### Sprint 0 — Destravar o piloto (semana de 03/09 a 09/09)

**Status:** implementado em 03/09/2026 no branch `worktree-sprint-0-rcd`, pendente de
verificação manual de ponta a ponta e das migrations `0008`, `0009` e `0010`.

**Hipótese:** o piloto é impossível hoje por custo e por falha silenciosa, não por falta de
funcionalidade.

**1. Extração por vaga, pontuação por perfil**

- `matching/prompt.py`: o prompt passa a pedir fatos da vaga — acrescentar `cursos_aceitos`,
  `periodo_minimo` e `experiencia_minima_anos`; remover o perfil do prompt.
- `matching/avaliacoes.py`: `AvaliacaoIA` vira `ExtracaoDaVaga`; `area`, `curso` e
  `periodo_experiencia` passam a ser calculados por comparação determinística com o `Perfil`,
  ao lado de `_compatibilidade_logistica`; `pontos_a_favor` e `pontos_contra` passam a ser
  montados a partir dessa comparação.
- Nova migration: `vagas.extracao jsonb`, `vagas.extraida_em`, `vagas.modelo_extracao`.
- `pipeline.py`: extrair uma vez, antes do laço de usuários, apenas as vagas que passam no
  pré-filtro de algum perfil e ainda não têm extração gravada.
- `AvaliadorEmLotes` continua responsável pela cota, agora sobre um volume fixo por dia.

**Critério:** o número de requisições ao Gemini por execução não muda ao dobrar o número de
usuários. Verificado por `test_dobrar_os_usuarios_nao_dobra_as_vagas_extraidas`.

**2. Nunca perder avaliação paga**

- `atender_usuario` grava as avaliações antes de tentar o envio, e o envio grava apenas `envios`
  e a ativação.
- Contador de falhas consecutivas de envio no perfil; ao atingir o limite, `ativo = false` com o
  evento `entregas_pausadas`, que o gatilho de `0005` já registra.

**Critério:** falha no Telegram não aumenta o custo do dia seguinte. Verificado por
`test_avaliacao_e_gravada_mesmo_quando_o_telegram_falha`.

**3. Aviso de execução**

- Passo final do workflow com `if: always()` enviando ao chat do operador o resumo — usuários
  atendidos, vagas enviadas, requisições ao Gemini — e, em falha, o link do run.
- `timeout-minutes` revisado depois de medir a duração real com o custo novo.

**Critério:** nenhum dia de silêncio passa despercebido durante o piloto.

**4. Nenhuma mensagem vazia, mas nenhum dia mudo**

- A mensagem "nenhuma vaga compatível hoje" não dizia o que aconteceria em seguida. Agora o dia
  sem vaga informa que a busca volta amanhã, para o estudante não concluir que o serviço morreu.
- Depois de `DIAS_DE_SILENCIO_ATE_AVISAR` dias sem nenhuma recomendação, a mesma mensagem ganha
  um parágrafo sugerindo ampliar cidade ou modalidade, no máximo uma vez por período.

**Critério:** nenhuma notificação sem informação, e nunca duas no mesmo dia. A sugestão ainda
não aponta para uma tela de edição de perfil, que só chega no sprint 3 — a redação informa sem
prometer um botão que não existe.

**Risco aceito:** uma notificação diária em dia vazio pode cansar. O piloto mede: se aparecer
bloqueio do bot concentrado em perfis com muitos dias vazios, a cadência volta à discussão.

**5. Telemetria que falha visível**

- `registerEvent` registra a falha no console e a expõe; `landing_visualizada` passa a ser
  emitido uma vez por sessão.

**Critério:** uma quebra da instrumentação é perceptível no mesmo dia.

### Sprint 1 — Medir valor de verdade (semana de 10/09 a 16/09)

**Hipótese:** entrega não é valor; sem clique e sem feedback, o piloto não produz dado.

**6. Link rastreável**

- Migration: `envios.token uuid not null default gen_random_uuid()`.
- Nova Edge Function `ir`: recebe o token, insere `vaga_aberta` com `perfil_id` e `vaga_id`, e
  responde 302 para a URL da vaga. Token desconhecido redireciona para a landing.
- `notification/formatador.py` passa a usar a URL rastreável, mantendo o domínio visível no texto.

**7. Feedback no Telegram**

- Teclado inline por vaga: `👍 Faz sentido`, `👎 Não serve`, `Candidatei-me`.
- `callback_data` no formato `<acao>:<token do envio>` — cabe nos 64 bytes.
- A Edge Function do webhook passa a tratar `callback_query` e grava `vaga_util`,
  `vaga_irrelevante` ou `candidatura_iniciada`, respondendo com `answerCallbackQuery`.
- O feedback é apenas registrado. **Não** altera ranking nesta fase.

**8. Leitura do funil**

- `docs/metricas.md` ganha a consulta do funil de valor e a de custo por usuário ativado.
- Comando `python -m radar metricas` imprime o funil da coorte e o custo do dia.

**Critério do Portão B':** para um usuário de teste, é possível reconstruir landing → cadastro →
vínculo → entrega → abertura → feedback → candidatura em uma consulta.

### Sprint 2 — Encurtar o tempo até a primeira entrega (semana de 17/09 a 23/09)

**Hipótese:** entregar em minutos em vez de no dia seguinte aumenta a ativação de produto.

**9. Busca imediata após o vínculo**

- `python -m radar rodar --perfil <id>` atende um único perfil.
- O workflow ganha um `input` opcional `perfil`.
- Ao gravar o `chat_id`, a Edge Function do webhook dispara o `workflow_dispatch` com esse input,
  usando um fine-grained token guardado em `supabase secrets` — o mesmo mecanismo já usado pelo
  cron-job.org.

**10. Primeira recomendação no onboarding**

- Depois do vínculo, a tela mostra "procurando sua primeira vaga" e passa a consultar `envios`.
- Chegando recomendação, ela é exibida na própria tela, com o mesmo link rastreável.
- Sem vaga adequada: **não** marcar ativação, explicar que nada seguro foi encontrado, informar
  quando será a próxima busca e oferecer ajuste de cidade ou modalidade.

**Metas:** mediana do tempo até a primeira entrega abaixo de 15 minutos; 80% dos vinculados com
recomendação em 24 horas. Aprovadas antes do piloto e não ajustadas depois.

### Sprint 3 — Controle, confiança e limpeza (semana de 24/09 a 30/09)

**11.** Página de perfil autenticada: editar curso, período, habilidades, áreas, cidade e
modalidade; pausar e retomar (`ativo`); desvincular o Telegram; excluir conta e dados; ver quando
ocorre a próxima busca.

**12.** Token de vínculo de uso único: a Edge Function passa a gravar `chat_id` e rotacionar
`token_vinculo` na mesma atualização, e recusa token já usado. A revinculação gera token novo pela
página de perfil.

**13.** Aviso curto de privacidade e finalidade na landing e no cadastro; exclusão sem contato
manual.

**14.** Decidir `cidades_aceitas`/`modalidades_aceitas`: implementar múltiplas cidades na edição
do perfil ou remover as colunas por migration. Não deixar como está.

**15.** Substituir `perfil_fixo.py` por um perfil sintético.

**Critério do Portão C':** o estudante controla o serviço e toda recomendação gera sinal
mensurável de qualidade.

### Sprint 4 — Piloto e prova (semanas de 01/10 a 14/10)

- Coorte fechada de 10 a 20 universitários de tecnologia buscando o primeiro estágio, duas
  semanas de uso.
- Cada canal com origem identificada — turma, comunidade, coordenação.
- Cinco entrevistas com o roteiro da seção 7.2 de `plano-melhorias-rcd.md`.
- Ao fim: substituir a faixa de tecnologias da landing por evidência real; a promessa comercial só
  cresce na proporção da prova.

### Sprint 5 — Monetização (a partir de 15/10, só após o Portão D)

Com o custo por usuário agora computável (Sprint 0 e 8), testar **uma** hipótese: o passe de busca
ativa por 30 ou 60 dias, que se ajusta ao churn estrutural — quando o estudante consegue o
estágio, o trabalho para o qual contratou o produto termina. Pagamento real com os dez primeiros,
compromisso definido antes do teste, hipótese promissora com três aceites. Sem página de três
planos.

## 6. O que não construir agora

Além da lista da seção 11 de `plano-melhorias-rcd.md`, ficam explicitamente fora:

- **Nova fonte de vagas.** Nada indica insuficiência de cobertura; indica falta de medição de
  utilidade.
- **Ajuste automático de ranking por feedback.** Sem volume, poucos eventos distorcem a
  recomendação. Registrar agora, usar depois.
- **Billing do Gemini.** O item 1 elimina a necessidade para a escala do piloto.
- **Novos pesos ou travas de pontuação.** A pontuação já está bem ajustada para o perfil nº 1; o
  próximo ajuste deve vir de `vaga_irrelevante` real, não de intuição.
- **Painel web de métricas.** Consulta SQL resolve na escala de 20 usuários.

## 7. Regra de execução

Mantida da seção 14 de `plano-melhorias-rcd.md`: cada entrega declara hipótese, métrica afetada,
implementação mínima, teste proporcional ao risco, verificação manual de ponta a ponta, evento de
produto correspondente e decisão de manter, ajustar ou remover.
