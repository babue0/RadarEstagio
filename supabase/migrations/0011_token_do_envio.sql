alter table envios add column token uuid not null default gen_random_uuid();

alter table envios add constraint envios_token_unico unique (token);
