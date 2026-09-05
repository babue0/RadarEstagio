alter table public.perfis
  add column aceita_emails boolean not null default false,
  add column termos_aceitos_em timestamptz,
  add column versao_dos_termos text,
  add constraint aceite_completo check (
    (termos_aceitos_em is null) = (versao_dos_termos is null)
  );

grant update (aceita_emails) on public.perfis to authenticated;
revoke insert (user_id, curso, periodo, habilidades, cidade, modalidade, areas_de_interesse)
  on public.perfis from authenticated;

create table public.cadastros_pendentes (
  user_id uuid primary key references auth.users(id) on delete cascade,
  cadastro jsonb not null,
  recebido_em timestamptz not null default now()
);
alter table public.cadastros_pendentes enable row level security;
revoke all on public.cadastros_pendentes from public, anon, authenticated;

create function public.validar_cadastro_radar(cadastro jsonb)
returns void
language plpgsql
set search_path = ''
as $$
declare
  perfil jsonb := cadastro->'perfil';
  lista text;
begin
  if jsonb_typeof(cadastro) is distinct from 'object'
    or cadastro->'aceitou_termos' is distinct from 'true'::jsonb
    or jsonb_typeof(cadastro->'versao_dos_termos') is distinct from 'string'
    or coalesce(cadastro->>'versao_dos_termos', '') !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
    or jsonb_typeof(cadastro->'aceita_emails') is distinct from 'boolean'
    or jsonb_typeof(perfil) is distinct from 'object' then
    raise exception 'cadastro ou aceite inválido' using errcode = '22023';
  end if;
  perform (cadastro->>'versao_dos_termos')::date;
  if jsonb_typeof(perfil->'curso') is distinct from 'string'
    or length(btrim(perfil->>'curso')) not between 2 and 200
    or jsonb_typeof(perfil->'cidade') is distinct from 'string'
    or length(btrim(perfil->>'cidade')) not between 2 and 120
    or coalesce(perfil->>'periodo', '') !~ '^[1-9][0-9]?$'
    or coalesce(perfil->>'modalidade', '') not in ('remoto', 'presencial', 'hibrido', 'indiferente') then
    raise exception 'perfil inválido' using errcode = '22023';
  end if;
  foreach lista in array array['habilidades', 'areas_de_interesse'] loop
    if jsonb_typeof(perfil->lista) is distinct from 'array' then
      raise exception 'lista inválida' using errcode = '22023';
    end if;
    if jsonb_array_length(perfil->lista) > 50 or exists (
      select 1 from jsonb_array_elements(perfil->lista) item
      where jsonb_typeof(item) <> 'string' or length(btrim(item #>> '{}')) not between 1 and 100
    ) then
      raise exception 'lista inválida' using errcode = '22023';
    end if;
  end loop;
  if jsonb_array_length(perfil->'habilidades') = 0 or exists (
    select 1 from jsonb_array_elements_text(perfil->'areas_de_interesse') area
    where area not in ('desenvolvimento_web', 'desenvolvimento_mobile', 'dados_ia',
      'infraestrutura_redes', 'seguranca', 'suporte_tecnico', 'qa_testes')
  ) then
    raise exception 'habilidades ou áreas inválidas' using errcode = '22023';
  end if;
  if coalesce(cadastro->>'sessao_id', '') !~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$' then
    raise exception 'sessão de cadastro inválida' using errcode = '22023';
  end if;
end;
$$;

create function public.criar_perfil_do_cadastro(dono uuid, cadastro jsonb, recebido_em timestamptz)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  perfil jsonb := cadastro->'perfil';
begin
  perform public.validar_cadastro_radar(cadastro);
  insert into public.perfis (user_id, curso, periodo, habilidades, cidade, modalidade,
    areas_de_interesse, aceita_emails, termos_aceitos_em, versao_dos_termos)
  values (dono, btrim(perfil->>'curso'), (perfil->>'periodo')::int,
    array(select btrim(x) from jsonb_array_elements_text(perfil->'habilidades') x),
    btrim(perfil->>'cidade'), perfil->>'modalidade',
    array(select x from jsonb_array_elements_text(perfil->'areas_de_interesse') x),
    (cadastro->>'aceita_emails')::boolean, recebido_em, cadastro->>'versao_dos_termos')
  on conflict (user_id) do nothing;
  update public.eventos_produto set sessao_id = (cadastro->>'sessao_id')::uuid
  where user_id = dono and origem = 'banco'
    and nome in ('conta_criada', 'email_confirmado', 'perfil_salvo') and sessao_id is null;
end;
$$;

create function public.processar_cadastro_radar()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  pendente public.cadastros_pendentes;
begin
  if tg_op = 'INSERT' and new.raw_user_meta_data ? 'cadastro_radar' then
    perform public.validar_cadastro_radar(new.raw_user_meta_data->'cadastro_radar');
    insert into public.cadastros_pendentes (user_id, cadastro)
      values (new.id, new.raw_user_meta_data->'cadastro_radar');
    update public.eventos_produto
      set sessao_id = (new.raw_user_meta_data->'cadastro_radar'->>'sessao_id')::uuid
      where user_id = new.id and nome = 'conta_criada' and origem = 'banco';
  end if;
  if new.email_confirmed_at is not null then
    select * into pendente from public.cadastros_pendentes where user_id = new.id for update;
    if found then
      perform public.criar_perfil_do_cadastro(new.id, pendente.cadastro, pendente.recebido_em);
      delete from public.cadastros_pendentes where user_id = new.id;
      update auth.users set raw_user_meta_data = raw_user_meta_data - 'cadastro_radar'
        where id = new.id;
    end if;
  end if;
  return new;
end;
$$;

create trigger z_processar_cadastro_radar
after insert or update of email_confirmed_at on auth.users
for each row execute function public.processar_cadastro_radar();

create function public.concluir_meu_cadastro(cadastro jsonb)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  if not exists (select 1 from auth.users where id = auth.uid() and email_confirmed_at is not null) then
    raise exception 'confirme seu e-mail' using errcode = '42501';
  end if;
  perform public.criar_perfil_do_cadastro(auth.uid(), cadastro, now());
end;
$$;

revoke all on function public.validar_cadastro_radar(jsonb) from public, anon, authenticated;
revoke all on function public.criar_perfil_do_cadastro(uuid, jsonb, timestamptz) from public, anon, authenticated;
revoke all on function public.processar_cadastro_radar() from public, anon, authenticated;
revoke all on function public.concluir_meu_cadastro(jsonb) from public, anon;
grant execute on function public.concluir_meu_cadastro(jsonb) to authenticated;
