alter table public.perfis
  add column areas_de_interesse text[];

alter table public.perfis
  add constraint perfis_areas_de_interesse_validas
    check (
      areas_de_interesse is null
      or areas_de_interesse <@ array[
        'desenvolvimento_web',
        'desenvolvimento_mobile',
        'dados_ia',
        'infraestrutura_redes',
        'seguranca',
        'suporte_tecnico',
        'qa_testes'
      ]::text[]
    );

grant insert (areas_de_interesse) on table public.perfis to authenticated;
grant update (areas_de_interesse) on table public.perfis to authenticated;
