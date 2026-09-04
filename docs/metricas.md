# Métricas de produto

## Eventos do funil

A migration `0005_eventos_produto.sql` cria `eventos_produto`, o catálogo fechado dos eventos
do plano e os gatilhos para marcos que precisam de uma fonte autoritativa. Cada evento registra
o instante, a origem e ao menos uma identidade entre sessão anônima, usuário ou perfil.

O navegador mantém um `sessao_id` aleatório no `localStorage`. Ele permite ligar a visita
anônima ao usuário quando o perfil é salvo, sem guardar e-mail, curso, cidade ou outro dado
pessoal nas propriedades do evento. Propriedades livres são limitadas a um objeto JSON de 4 KB.

| Origem | Eventos emitidos agora |
|---|---|
| Web | `landing_visualizada`, `cta_cadastro_aberto`, as três etapas concluídas, `perfil_salvo`, `telegram_aberto` |
| Gatilhos do banco | `conta_criada`, `email_confirmado`, `perfil_salvo`, `telegram_vinculado`, `primeira_recomendacao_enviada`, `entregas_pausadas` |
| Telegram | `vaga_aberta`, `vaga_util`, `vaga_irrelevante`, `candidatura_iniciada` |

`vaga_aberta` vem da Edge Function `ir`. Cada linha de `envios` guarda um `token` único e o link
da mensagem aponta para `ir?t=<token>`; a função registra o evento com `perfil_id` e `vaga_id` e
responde 302 para a URL da vaga. Token desconhecido — link antigo, envio que não chegou a ser
gravado — redireciona para a landing sem registrar evento. Cliques repetidos geram linhas
repetidas de propósito: as consultas de funil usam a primeira ocorrência, e a contagem bruta mede
reincidência.

`vaga_util`, `vaga_irrelevante` e `candidatura_iniciada` vêm dos botões da mensagem, tratados pela
Edge Function `telegram-webhook`. O `callback_data` é `<acao>:<token do envio>`, o mesmo token do
link, então cada clique identifica perfil e vaga sem depender do texto da mensagem. O clique só é
aceito quando o chat que clicou é o chat vinculado ao perfil daquele envio.

O motivo da recusa é gravado nas `propriedades` do **mesmo** `vaga_irrelevante`, não em um segundo
evento: o 👎 já registra a recusa na hora — para não perder o sinal de quem não responde a segunda
pergunta — e o motivo apenas completa a linha existente. Assim a contagem de `vaga_irrelevante`
continua sendo a contagem de recusas, e `propriedades->>'motivo'` nulo significa "recusou e não
disse por quê".

`perfil_salvo` pode aparecer duas vezes: o gatilho garante o marco autoritativo e o evento web
liga a sessão anônima ao usuário. Consultas de funil devem usar o primeiro instante por evento,
não contar linhas brutas.

Esta consulta reconstrói a primeira ocorrência de cada etapa por usuário, incluindo os eventos
anônimos da sessão que posteriormente salvou um perfil:

```sql
with sessoes_identificadas as (
  select sessao_id, min(user_id::text)::uuid as user_id
  from public.eventos_produto
  where sessao_id is not null and user_id is not null
  group by sessao_id
  having count(distinct user_id) = 1
), eventos_identificados as (
  select
    coalesce(evento.user_id, sessao.user_id) as user_id,
    evento.nome,
    evento.ocorrido_em
  from public.eventos_produto as evento
  left join sessoes_identificadas as sessao using (sessao_id)
), funil as (
  select
    user_id,
    min(ocorrido_em) filter (where nome = 'landing_visualizada') as landing_visualizada_em,
    min(ocorrido_em) filter (where nome = 'cta_cadastro_aberto') as cadastro_aberto_em,
    min(ocorrido_em) filter (where nome = 'etapa_perfil_concluida') as perfil_concluido_em,
    min(ocorrido_em) filter (where nome = 'etapa_habilidades_concluida') as habilidades_concluidas_em,
    min(ocorrido_em) filter (where nome = 'etapa_preferencias_concluida') as preferencias_concluidas_em,
    min(ocorrido_em) filter (where nome = 'conta_criada') as conta_criada_em,
    min(ocorrido_em) filter (where nome = 'email_confirmado') as email_confirmado_em,
    min(ocorrido_em) filter (where nome = 'perfil_salvo') as perfil_salvo_em,
    min(ocorrido_em) filter (where nome = 'telegram_aberto') as telegram_aberto_em,
    min(ocorrido_em) filter (where nome = 'telegram_vinculado') as telegram_vinculado_em,
    min(ocorrido_em) filter (
      where nome = 'primeira_recomendacao_enviada'
    ) as primeira_recomendacao_em,
    min(ocorrido_em) filter (where nome = 'vaga_aberta') as primeira_vaga_aberta_em,
    min(ocorrido_em) filter (where nome = 'vaga_util') as primeira_vaga_util_em,
    min(ocorrido_em) filter (where nome = 'candidatura_iniciada') as primeira_candidatura_em
  from eventos_identificados
  where user_id is not null
  group by user_id
)
select *
from funil
order by conta_criada_em desc nulls last;
```

## Ativação operacional e ativação de produto

O vocabulário canônico está em [`CONTEXT.md`](../CONTEXT.md). O Radar separa dois marcos:

- **Ativação operacional:** primeira entrega bem-sucedida no Telegram contendo ao menos uma
  recomendação. Confirma que o fluxo técnico funcionou, mas não que o estudante percebeu valor.
- **Ativação de produto:** primeira abertura de uma vaga recomendada. É o primeiro sinal
  observável de interesse e será reforçado depois por feedback positivo ou candidatura.

Criar a conta, preencher o perfil, confirmar o e-mail e vincular o Telegram são etapas do funil,
mas ainda não são ativação. Uma mensagem informando que nenhuma vaga foi encontrada também não
conta como ativação operacional.

A fonte de verdade da ativação operacional é `perfis.ativado_em`. O nome do campo é mantido por
compatibilidade com o schema atual. O pipeline o preenche somente depois de o Telegram aceitar a
entrega e na mesma transação que grava os respectivos registros em `envios`. O valor nunca é
sobrescrito; reprocessamentos não geram uma segunda ativação operacional.

A fonte de verdade da ativação de produto é a primeira ocorrência de `vaga_aberta` por usuário.
Ela depende do link rastreável: sem `URL_DE_RASTREIO` configurado, a mensagem volta a apontar
direto para a fonte e nenhuma abertura é registrada.

A migration `0003_evento_ativacao.sql` também preenche o campo de perfis antigos a partir do
primeiro `envios.enviada_em` já registrado.

## Métricas derivadas atuais

### Taxa de ativação operacional em 7 dias

Percentual dos perfis criados em uma coorte que receberam a primeira recomendação em até
7 dias. Perfis com menos de 7 dias devem ficar fora do denominador até completarem a janela.

### Tempo até a primeira entrega

Mediana, em horas, entre `criado_em` e `ativado_em` para os perfis ativados dentro da janela de
7 dias. Essa métrica mede velocidade operacional, não valor percebido. A mediana evita que poucos
casos muito atrasados distorçam a leitura.

Esta consulta calcula as duas métricas para a coorte madura dos últimos 30 dias:

```sql
with coorte as (
  select criado_em, ativado_em
  from public.perfis
  where criado_em >= now() - interval '37 days'
    and criado_em < now() - interval '7 days'
), ativados as (
  select criado_em, ativado_em
  from coorte
  where ativado_em <= criado_em + interval '7 days'
)
select
  round(
    100.0 * (select count(*) from ativados) / nullif((select count(*) from coorte), 0),
    1
  ) as taxa_ativacao_operacional_7d_percentual,
  round(
    (
      percentile_cont(0.5) within group (
        order by extract(epoch from (ativado_em - criado_em)) / 3600
      )
    )::numeric,
    1
  ) as tempo_ate_primeira_entrega_mediano_horas
from ativados;
```

## Funil de valor da coorte

Da entrega ao resultado: quantos perfis chegaram a cada etapa e quantas recomendações viraram
abertura, feedback e candidatura. `python -m radar metricas` imprime exatamente este funil para os
perfis criados nos últimos 30 dias, junto do custo de extração do período.

```sql
with coorte as (
  select id, telegram_chat_id, ativado_em
  from public.perfis
  where criado_em >= now() - interval '30 days'
), eventos as (
  select evento.perfil_id, evento.nome
  from public.eventos_produto as evento
  join coorte on coorte.id = evento.perfil_id
)
select
  (select count(*) from coorte) as perfis_criados,
  (select count(*) from coorte where telegram_chat_id is not null) as perfis_vinculados,
  (select count(*) from coorte where ativado_em is not null) as perfis_ativados,
  (select count(distinct perfil_id) from eventos where nome = 'vaga_aberta')
    as perfis_com_vaga_aberta,
  (select count(distinct perfil_id) from eventos where nome = 'vaga_util')
    as perfis_com_vaga_util,
  (select count(distinct perfil_id) from eventos where nome = 'candidatura_iniciada')
    as perfis_com_candidatura,
  (select count(*) from public.envios e join coorte on coorte.id = e.perfil_id) as vagas_enviadas,
  (select count(*) from eventos where nome = 'vaga_aberta') as vagas_abertas,
  (select count(*) from eventos where nome = 'vaga_util') as vagas_uteis,
  (select count(*) from eventos where nome = 'vaga_irrelevante') as vagas_irrelevantes,
  (select count(*) from eventos where nome = 'candidatura_iniciada') as candidaturas;
```

## Custo por usuário ativado

Cada vaga é extraída uma vez e a extração serve todos os perfis, então o custo do período é o
número de vagas extraídas, não o número de usuários. As requisições ao Gemini são menos do que as
vagas extraídas, porque a extração vai em lotes de `GEMINI_VAGAS_POR_LOTE` — o número exato de
requisições da execução do dia sai no resumo enviado ao chat de operação.

```sql
select
  (select count(*) from public.vagas where extraida_em >= now() - interval '30 days')
    as vagas_extraidas,
  (select count(*) from public.perfis
    where criado_em >= now() - interval '30 days' and ativado_em is not null)
    as usuarios_ativados,
  round(
    (select count(*) from public.vagas where extraida_em >= now() - interval '30 days')::numeric
    / nullif(
      (select count(*) from public.perfis
        where criado_em >= now() - interval '30 days' and ativado_em is not null),
      0
    ),
    1
  ) as vagas_extraidas_por_ativado;
```

## Recusa por motivo

Fecha o laço com o viés registrado na seção 7 de [`auditoria-rcd.md`](auditoria-rcd.md): se a
recusa se concentrar em vagas que declaram uma ou duas tecnologias, o teto para anúncio raso
deixa de ser intuição e vira correção com dado. `motivo` nulo é recusa sem segunda resposta.

```sql
select
  coalesce(evento.propriedades->>'motivo', 'sem_motivo') as motivo,
  count(*) as recusas,
  count(*) filter (
    where jsonb_array_length(
      coalesce(vaga.extracao->'habilidades_obrigatorias', '[]'::jsonb)
    ) <= 2
  ) as recusas_de_anuncio_raso
from public.eventos_produto as evento
join public.vagas as vaga on vaga.id = evento.vaga_id
where evento.nome = 'vaga_irrelevante'
  and evento.ocorrido_em >= now() - interval '30 days'
group by 1
order by recusas desc, motivo;
```

## Métricas derivadas de interação

- **Taxa de ativação de produto em 7 dias:** percentual dos perfis criados que abrem ao menos uma
  recomendação em até 7 dias.
- **Tempo até o valor:** mediana entre `perfis.criado_em` e o primeiro `vaga_aberta`.
- **Taxa de vagas úteis:** recomendações com feedback positivo ou candidatura atribuída sobre o
  total entregue.
- **Candidaturas atribuídas por usuário com ativação operacional por semana:** resultado final de
  negócio.

Essas métricas devem ser segmentadas por modalidade, cidade ou período do curso apenas quando
houver volume suficiente para não expor indivíduos nem tirar conclusões de amostras pequenas.
