alter table public.vagas
  add column extracao jsonb,
  add column extraida_em timestamptz,
  add column modelo_extracao text;

create index vagas_sem_extracao_idx
  on public.vagas (coletada_em)
  where extracao is null;
