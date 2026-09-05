alter table public.perfis
  add column excluida_em timestamptz;

create index perfis_excluida_em_idx
  on public.perfis (excluida_em)
  where excluida_em is not null;

create function public.desvincular_meu_telegram()
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  update public.perfis
  set telegram_chat_id = null,
      token_vinculo = gen_random_uuid(),
      atualizado_em = now()
  where user_id = auth.uid();
end;
$$;

create function public.excluir_minha_conta()
returns timestamptz
language plpgsql
security definer
set search_path = ''
as $$
declare
  dono uuid := auth.uid();
  marcada timestamptz;
begin
  if dono is null then
    raise exception 'sem sessão';
  end if;
  update public.perfis
  set excluida_em = coalesce(excluida_em, now()),
      telegram_chat_id = null,
      token_vinculo = gen_random_uuid(),
      atualizado_em = now()
  where user_id = dono
  returning excluida_em into marcada;
  return marcada;
end;
$$;

create function public.cancelar_exclusao_da_minha_conta()
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  update public.perfis
  set excluida_em = null,
      atualizado_em = now()
  where user_id = auth.uid() and excluida_em is not null;
end;
$$;

revoke all on function public.desvincular_meu_telegram() from public, anon;
revoke all on function public.excluir_minha_conta() from public, anon;
revoke all on function public.cancelar_exclusao_da_minha_conta() from public, anon;
grant execute on function public.desvincular_meu_telegram() to authenticated;
grant execute on function public.excluir_minha_conta() to authenticated;
grant execute on function public.cancelar_exclusao_da_minha_conta() to authenticated;

drop policy "usuario edita o proprio perfil" on public.perfis;
create policy "usuario edita o proprio perfil"
  on public.perfis for update
  using (auth.uid() = user_id and excluida_em is null)
  with check (auth.uid() = user_id and excluida_em is null);
