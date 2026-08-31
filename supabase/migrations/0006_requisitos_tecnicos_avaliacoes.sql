alter table public.avaliacoes
  add column requisitos_atendidos text[] not null default '{}',
  add column requisitos_nao_atendidos text[] not null default '{}',
  add column requisitos_tecnicos_analisados boolean not null default false;
