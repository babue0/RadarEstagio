create function public.verificar_perfil_da_interacao()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if new.nome in ('vaga_aberta', 'vaga_util', 'vaga_irrelevante', 'candidatura_iniciada') then
    perform 1 from public.perfis
      where id = new.perfil_id and user_id = new.user_id
        and ativo and excluida_em is null and telegram_chat_id is not null
      for share;
    if not found then
      raise exception 'perfil indisponível para interação' using errcode = '42501';
    end if;
  end if;
  return new;
end;
$$;

create trigger verificar_perfil_da_interacao
before insert on public.eventos_produto
for each row execute function public.verificar_perfil_da_interacao();
revoke all on function public.verificar_perfil_da_interacao() from public, anon, authenticated;

create policy "conta excluida nao registra eventos"
on public.eventos_produto as restrictive for insert to authenticated
with check (not exists (
  select 1 from public.perfis where user_id = auth.uid() and excluida_em is not null
));
