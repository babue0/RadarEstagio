alter table public.perfis
  add column falhas_de_envio int not null default 0
    check (falhas_de_envio >= 0);
