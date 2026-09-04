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
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  dono uuid := auth.uid();
begin
  if dono is null then
    raise exception 'sem sessão';
  end if;
  delete from auth.users where id = dono;
end;
$$;

revoke all on function public.desvincular_meu_telegram() from public, anon;
revoke all on function public.excluir_minha_conta() from public, anon;
grant execute on function public.desvincular_meu_telegram() to authenticated;
grant execute on function public.excluir_minha_conta() to authenticated;
