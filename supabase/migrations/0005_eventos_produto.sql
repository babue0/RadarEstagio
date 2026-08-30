create type public.nome_evento_produto as enum (
  'landing_visualizada',
  'cta_cadastro_aberto',
  'etapa_perfil_concluida',
  'etapa_habilidades_concluida',
  'etapa_preferencias_concluida',
  'conta_criada',
  'email_confirmado',
  'perfil_salvo',
  'telegram_aberto',
  'telegram_vinculado',
  'primeira_recomendacao_enviada',
  'vaga_aberta',
  'vaga_util',
  'vaga_irrelevante',
  'candidatura_iniciada',
  'entregas_pausadas'
);

create table public.eventos_produto (
  id             bigint generated always as identity primary key,
  nome           public.nome_evento_produto not null,
  origem         text not null default 'web' check (origem in ('web', 'banco', 'telegram')),
  sessao_id      uuid,
  user_id        uuid references auth.users (id) on delete cascade,
  perfil_id      uuid references public.perfis (id) on delete cascade,
  vaga_id        bigint references public.vagas (id) on delete set null,
  propriedades  jsonb not null default '{}'::jsonb,
  ocorrido_em    timestamptz not null default now(),
  check (jsonb_typeof(propriedades) = 'object'),
  check (octet_length(propriedades::text) <= 4096),
  check (num_nonnulls(sessao_id, user_id, perfil_id) >= 1)
);

create index eventos_produto_nome_ocorrido_idx
  on public.eventos_produto (nome, ocorrido_em);

create index eventos_produto_sessao_idx
  on public.eventos_produto (sessao_id, ocorrido_em)
  where sessao_id is not null;

create index eventos_produto_usuario_idx
  on public.eventos_produto (user_id, ocorrido_em)
  where user_id is not null;

create index eventos_produto_perfil_idx
  on public.eventos_produto (perfil_id, ocorrido_em)
  where perfil_id is not null;

alter table public.eventos_produto enable row level security;

revoke all on table public.eventos_produto from anon;
revoke all on table public.eventos_produto from authenticated;

grant insert (nome, sessao_id, user_id, propriedades)
  on table public.eventos_produto to anon, authenticated;

grant usage, select on sequence public.eventos_produto_id_seq to anon, authenticated;

create policy "visitante registra eventos publicos"
  on public.eventos_produto
  for insert
  to anon
  with check (
    origem = 'web'
    and sessao_id is not null
    and user_id is null
    and perfil_id is null
    and vaga_id is null
    and nome in (
      'landing_visualizada',
      'cta_cadastro_aberto',
      'etapa_perfil_concluida',
      'etapa_habilidades_concluida',
      'etapa_preferencias_concluida'
    )
  );

create policy "usuario registra eventos do proprio funil"
  on public.eventos_produto
  for insert
  to authenticated
  with check (
    origem = 'web'
    and sessao_id is not null
    and user_id = auth.uid()
    and perfil_id is null
    and vaga_id is null
    and nome in (
      'landing_visualizada',
      'cta_cadastro_aberto',
      'etapa_perfil_concluida',
      'etapa_habilidades_concluida',
      'etapa_preferencias_concluida',
      'perfil_salvo',
      'telegram_aberto'
    )
  );

create function public.registrar_eventos_de_conta()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if tg_op = 'INSERT' then
    insert into public.eventos_produto (nome, origem, user_id, ocorrido_em)
    values ('conta_criada', 'banco', new.id, coalesce(new.created_at, now()));
    if new.email_confirmed_at is not null then
      insert into public.eventos_produto (nome, origem, user_id, ocorrido_em)
      values ('email_confirmado', 'banco', new.id, new.email_confirmed_at);
    end if;
  elsif old.email_confirmed_at is null and new.email_confirmed_at is not null then
    insert into public.eventos_produto (nome, origem, user_id, ocorrido_em)
    values ('email_confirmado', 'banco', new.id, new.email_confirmed_at);
  end if;
  return new;
end;
$$;

create trigger registrar_eventos_de_conta
after insert or update of email_confirmed_at on auth.users
for each row execute function public.registrar_eventos_de_conta();

revoke all on function public.registrar_eventos_de_conta() from public, anon, authenticated;

create function public.registrar_eventos_de_perfil()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if tg_op = 'INSERT' then
    insert into public.eventos_produto
      (nome, origem, user_id, perfil_id, ocorrido_em)
    values
      ('perfil_salvo', 'banco', new.user_id, new.id, new.criado_em);
    if new.telegram_chat_id is not null then
      insert into public.eventos_produto
        (nome, origem, user_id, perfil_id, ocorrido_em)
      values
        ('telegram_vinculado', 'banco', new.user_id, new.id, new.criado_em);
    end if;
    if new.ativado_em is not null then
      insert into public.eventos_produto
        (nome, origem, user_id, perfil_id, ocorrido_em)
      values
        ('primeira_recomendacao_enviada', 'banco', new.user_id, new.id, new.ativado_em);
    end if;
    if not new.ativo then
      insert into public.eventos_produto
        (nome, origem, user_id, perfil_id, ocorrido_em)
      values
        ('entregas_pausadas', 'banco', new.user_id, new.id, new.criado_em);
    end if;
  else
    if old.telegram_chat_id is null and new.telegram_chat_id is not null then
      insert into public.eventos_produto
        (nome, origem, user_id, perfil_id, ocorrido_em)
      values
        ('telegram_vinculado', 'banco', new.user_id, new.id, now());
    end if;
    if old.ativado_em is null and new.ativado_em is not null then
      insert into public.eventos_produto
        (nome, origem, user_id, perfil_id, ocorrido_em)
      values
        ('primeira_recomendacao_enviada', 'banco', new.user_id, new.id, new.ativado_em);
    end if;
    if old.ativo and not new.ativo then
      insert into public.eventos_produto
        (nome, origem, user_id, perfil_id, ocorrido_em)
      values
        ('entregas_pausadas', 'banco', new.user_id, new.id, now());
    end if;
  end if;
  return new;
end;
$$;

create trigger registrar_eventos_de_perfil
after insert or update of telegram_chat_id, ativado_em, ativo on public.perfis
for each row execute function public.registrar_eventos_de_perfil();

revoke all on function public.registrar_eventos_de_perfil() from public, anon, authenticated;

insert into public.eventos_produto (nome, origem, user_id, ocorrido_em)
select 'conta_criada', 'banco', id, created_at
from auth.users;

insert into public.eventos_produto (nome, origem, user_id, ocorrido_em)
select 'email_confirmado', 'banco', id, email_confirmed_at
from auth.users
where email_confirmed_at is not null;

insert into public.eventos_produto
  (nome, origem, user_id, perfil_id, ocorrido_em)
select 'perfil_salvo', 'banco', user_id, id, criado_em
from public.perfis;

insert into public.eventos_produto
  (nome, origem, user_id, perfil_id, ocorrido_em)
select 'telegram_vinculado', 'banco', user_id, id, atualizado_em
from public.perfis
where telegram_chat_id is not null;

insert into public.eventos_produto
  (nome, origem, user_id, perfil_id, ocorrido_em)
select 'primeira_recomendacao_enviada', 'banco', user_id, id, ativado_em
from public.perfis
where ativado_em is not null;

insert into public.eventos_produto
  (nome, origem, user_id, perfil_id, ocorrido_em)
select 'entregas_pausadas', 'banco', user_id, id, atualizado_em
from public.perfis
where not ativo;
