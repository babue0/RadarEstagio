create table perfis (
  id                uuid primary key default gen_random_uuid(),
  user_id           uuid not null unique references auth.users (id) on delete cascade,
  curso             text not null,
  periodo           int  not null check (periodo >= 1),
  habilidades       text[] not null check (cardinality(habilidades) >= 1),
  cidade            text not null,
  modalidade        text not null check (modalidade in ('remoto', 'presencial', 'hibrido', 'indiferente')),
  telegram_chat_id  text unique,
  token_vinculo     uuid not null unique default gen_random_uuid(),
  ativo             boolean not null default true,
  criado_em         timestamptz not null default now(),
  atualizado_em     timestamptz not null default now()
);

create table vagas (
  id            bigint generated always as identity primary key,
  fonte         text not null,
  id_externo    text not null,
  titulo        text not null,
  empresa       text not null,
  localizacao   text not null,
  descricao     text not null,
  url           text not null,
  publicada_em  timestamptz not null,
  modalidade    text check (modalidade in ('remoto', 'presencial', 'hibrido', 'indiferente')),
  coletada_em   timestamptz not null default now(),
  unique (fonte, id_externo)
);

create table avaliacoes (
  id                bigint generated always as identity primary key,
  perfil_id         uuid   not null references perfis (id) on delete cascade,
  vaga_id           bigint not null references vagas (id) on delete cascade,
  nota              int    not null check (nota between 0 and 100),
  pontos_a_favor    text[] not null default '{}',
  pontos_contra     text[] not null default '{}',
  alerta_pegadinha  text,
  modelo            text   not null,
  avaliada_em       timestamptz not null default now(),
  unique (perfil_id, vaga_id)
);

create table envios (
  perfil_id   uuid   not null references perfis (id) on delete cascade,
  vaga_id     bigint not null references vagas (id) on delete cascade,
  enviada_em  timestamptz not null default now(),
  primary key (perfil_id, vaga_id)
);

alter table perfis enable row level security;

create policy "usuario ve o proprio perfil"
  on perfis for select using (auth.uid() = user_id);

create policy "usuario cria o proprio perfil"
  on perfis for insert with check (auth.uid() = user_id);

create policy "usuario edita o proprio perfil"
  on perfis for update using (auth.uid() = user_id);

alter table vagas enable row level security;
alter table avaliacoes enable row level security;
alter table envios enable row level security;
