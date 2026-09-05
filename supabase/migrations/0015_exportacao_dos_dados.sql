create function public.baixar_meus_dados()
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  dono uuid := auth.uid();
  resultado jsonb;
begin
  if dono is null then
    raise exception 'sem sessão' using errcode = '42501';
  end if;
  select jsonb_build_object(
    'exportado_em', now(),
    'conta', (select jsonb_build_object('email', u.email, 'criada_em', u.created_at,
      'email_confirmado_em', u.email_confirmed_at) from auth.users u where u.id = dono),
    'perfil', (select to_jsonb(p) - 'token_vinculo' from public.perfis p where p.user_id = dono),
    'cadastro_pendente', (select c.cadastro from public.cadastros_pendentes c where c.user_id = dono),
    'avaliacoes', coalesce((select jsonb_agg(to_jsonb(a)) from public.avaliacoes a
      join public.perfis p on p.id = a.perfil_id where p.user_id = dono), '[]'::jsonb),
    'envios', coalesce((select jsonb_agg(to_jsonb(e) - 'token') from public.envios e
      join public.perfis p on p.id = e.perfil_id where p.user_id = dono), '[]'::jsonb),
    'eventos', coalesce((select jsonb_agg(to_jsonb(e)) from public.eventos_produto e
      where e.user_id = dono or e.perfil_id in (select id from public.perfis where user_id = dono)), '[]'::jsonb)
  ) into resultado;
  return resultado;
end;
$$;

revoke all on function public.baixar_meus_dados() from public, anon;
grant execute on function public.baixar_meus_dados() to authenticated;
