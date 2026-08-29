# Métricas de produto

## Evento de ativação

O evento de ativação do Radar é a **primeira entrega bem-sucedida no Telegram contendo ao
menos uma vaga recomendada para o perfil**.

Esse momento representa o primeiro valor percebido: o estudante recebeu uma oportunidade
selecionada para ele no canal prometido pelo produto. Criar a conta, preencher o perfil,
confirmar o e-mail e vincular o Telegram são etapas necessárias, mas ainda não são ativação.
Uma mensagem informando que nenhuma vaga foi encontrada também não conta.

A fonte de verdade é `perfis.ativado_em`. O pipeline preenche o campo somente depois de o
Telegram aceitar a entrega e na mesma transação que grava os respectivos registros em
`envios`. O valor nunca é sobrescrito. Assim, reprocessamentos não geram uma segunda ativação.

A migration `0003_evento_ativacao.sql` também preenche o campo de perfis antigos a partir do
primeiro `envios.enviada_em` já registrado.

## Métricas derivadas

### Taxa de ativação em 7 dias

Percentual dos perfis criados em uma coorte que receberam a primeira entrega relevante em até
7 dias. Perfis com menos de 7 dias devem ficar fora do denominador até completarem a janela.

### Tempo até o valor

Mediana, em horas, entre `criado_em` e `ativado_em` para os perfis ativados dentro da janela de
7 dias. A mediana evita que poucos casos muito atrasados distorçam a leitura.

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
  ) as taxa_ativacao_7d_percentual,
  round(
    (
      percentile_cont(0.5) within group (
        order by extract(epoch from (ativado_em - criado_em)) / 3600
      )
    )::numeric,
    1
  ) as tempo_ate_valor_mediano_horas
from ativados;
```

Essas métricas devem ser segmentadas por modalidade, cidade ou período do curso apenas quando
houver volume suficiente para não expor indivíduos nem tirar conclusões de amostras pequenas.
