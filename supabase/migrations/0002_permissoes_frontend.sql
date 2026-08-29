revoke all on table public.perfis from anon;
revoke all on table public.perfis from authenticated;

grant select on table public.perfis to authenticated;
grant insert (user_id, curso, periodo, habilidades, cidade, modalidade) on table public.perfis to authenticated;
grant update (curso, periodo, habilidades, cidade, modalidade, ativo, atualizado_em) on table public.perfis to authenticated;
