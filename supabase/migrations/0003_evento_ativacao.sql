alter table public.perfis
  add column ativado_em timestamptz;

update public.perfis as perfil
set ativado_em = primeiro_envio.enviado_em
from (
  select perfil_id, min(enviada_em) as enviado_em
  from public.envios
  group by perfil_id
) as primeiro_envio
where perfil.id = primeiro_envio.perfil_id;

create index perfis_ativado_em_idx
  on public.perfis (ativado_em)
  where ativado_em is not null;
