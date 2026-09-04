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
| Telegram | `vaga_aberta` |
| Contrato reservado | `vaga_util`, `vaga_irrelevante`, `candidatura_iniciada` |

`vaga_aberta` vem da Edge Function `ir`. Cada linha de `envios` guarda um `token` único e o link
da mensagem aponta para `ir?t=<token>`; a função registra o evento com `user_id`, `perfil_id` e
`vaga_id` e responde 302 para a URL da vaga. O `user_id` não é redundante: a consulta do funil
identifica a pessoa por `user_id` ou `sessao_id` e descarta linhas sem os dois, então um evento
gravado só com `perfil_id` entraria no banco e sumiria da métrica. Requisição `HEAD` redireciona
sem registrar, para que verificador de link não vire abertura. Token desconhecido — link antigo, envio que não chegou a ser
gravado — redireciona para a landing sem registrar evento. Cliques repetidos geram linhas
repetidas de propósito: as consultas de funil usam a primeira ocorrência, e a contagem bruta mede
reincidência.

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

## Métricas pendentes de interação

Quando `vaga_aberta` passar a ser emitido, acompanhar:

- **Taxa de ativação de produto em 7 dias:** percentual dos perfis criados que abrem ao menos uma
  recomendação em até 7 dias.
- **Tempo até o valor:** mediana entre `perfis.criado_em` e o primeiro `vaga_aberta`.
- **Taxa de vagas úteis:** recomendações com feedback positivo ou candidatura atribuída sobre o
  total entregue.
- **Candidaturas atribuídas por usuário com ativação operacional por semana:** resultado final de
  negócio.

Essas métricas devem ser segmentadas por modalidade, cidade ou período do curso apenas quando
houver volume suficiente para não expor indivíduos nem tirar conclusões de amostras pequenas.
