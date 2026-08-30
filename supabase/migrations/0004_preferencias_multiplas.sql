alter table public.perfis
  add column cidades_aceitas text[],
  add column modalidades_aceitas text[];
update public.perfis
set
  cidades_aceitas = array[cidade],
  modalidades_aceitas = case modalidade
    when 'indiferente' then array['remoto', 'hibrido', 'presencial']
    else array[modalidade]
  end;
alter table public.perfis
  add constraint perfis_cidades_aceitas_preenchidas
    check (cidades_aceitas is null or cardinality(cidades_aceitas) >= 1),
  add constraint perfis_modalidades_aceitas_preenchidas
    check (modalidades_aceitas is null or cardinality(modalidades_aceitas) >= 1),
  add constraint perfis_modalidades_aceitas_validas
    check (
      modalidades_aceitas is null
      or modalidades_aceitas <@ array['remoto', 'hibrido', 'presencial']::text[]
    );
grant insert (
  user_id, curso, periodo, habilidades, cidade, modalidade,
  cidades_aceitas, modalidades_aceitas
) on table public.perfis to authenticated;
grant update (
  curso, periodo, habilidades, cidade, modalidade,
  cidades_aceitas, modalidades_aceitas, ativo, atualizado_em
) on table public.perfis to authenticated;
