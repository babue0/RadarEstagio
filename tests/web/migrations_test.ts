import assert from "assert";
import { PGlite } from "pglite";

Deno.test("cadastro, confirmação, permissões e exportação com PostgreSQL isolado", async () => {
  const db = new PGlite();
  try {
    await db.exec(`
      create role anon;
      create role authenticated;
      create schema auth;
      create table auth.users (
        id uuid primary key, email text, created_at timestamptz default now(),
        email_confirmed_at timestamptz, raw_user_meta_data jsonb default '{}'
      );
      create function auth.uid() returns uuid language sql stable as
        $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
      grant usage on schema public, auth to authenticated, anon;
      grant execute on function auth.uid() to authenticated, anon;
    `);
    const directory = new URL("../../supabase/migrations/", import.meta.url);
    const files = [];
    for await (const entry of Deno.readDir(directory)) {
      if (entry.name.endsWith(".sql")) files.push(entry.name);
    }
    for (const file of files.sort()) {
      await db.exec(await Deno.readTextFile(new URL(file, directory)));
    }
    const dono = "00000000-0000-4000-8000-000000000001";
    const outro = "00000000-0000-4000-8000-000000000002";
    const sessao = "00000000-0000-4000-8000-000000000003";
    const cadastro = {
      perfil: {
        curso: "Computação",
        periodo: 3,
        habilidades: ["Python"],
        cidade: "Recife, PE",
        modalidade: "remoto",
        areas_de_interesse: ["dados_ia"],
      },
      aceitou_termos: true,
      aceita_emails: false,
      versao_dos_termos: "2026-09-05",
      sessao_id: sessao,
    };
    const count = async (table: string) =>
      Number(
        (await db.query<{ n: number }>(
          `select count(*) n from public.${table}`,
        )).rows[0].n,
      );
    await db.query(
      "insert into auth.users(id,email,raw_user_meta_data) values ($1,$2,$3)",
      [dono, "dono@example.com", { cadastro_radar: cadastro }],
    );
    assert.equal(await count("perfis"), 0);
    assert.equal(await count("cadastros_pendentes"), 1);
    await db.query(
      "update auth.users set raw_user_meta_data = '{}' where id = $1",
      [dono],
    );
    await db.query(
      "update auth.users set email_confirmed_at = now() where id = $1",
      [dono],
    );
    assert.equal(await count("perfis"), 1);
    assert.equal(await count("cadastros_pendentes"), 0);
    let saved = (await db.query<
      {
        id: string;
        cidade: string;
        aceita_emails: boolean;
        versao_dos_termos: string;
        termos_aceitos_em: string;
      }
    >("select * from perfis where user_id = $1", [dono]))
      .rows[0];
    assert.equal(saved.cidade, "Recife, PE");
    assert.equal(saved.aceita_emails, false);
    assert.equal(saved.versao_dos_termos, "2026-09-05");
    assert.ok(saved.termos_aceitos_em);
    const events = (await db.query<{ nome: string; sessao_id: string }>(
      "select nome, sessao_id from eventos_produto where user_id = $1",
      [dono],
    )).rows;
    assert.equal(events.length, 3);
    assert.ok(events.every((event) => event.sessao_id === sessao));
    await db.query(
      "update auth.users set email_confirmed_at = now() where id = $1",
      [dono],
    );
    assert.equal(await count("perfis"), 1);
    await db.query(
      "insert into auth.users(id,email,email_confirmed_at,raw_user_meta_data) values ($1,$2,now(),$3)",
      [outro, "outro@example.com", {
        cadastro_radar: { ...cadastro, versao_dos_termos: "2026-09-06" },
      }],
    );
    await db.query(
      "update perfis set cidade = 'Cidade privada' where user_id = $1",
      [outro],
    );
    const metadata =
      (await db.query<{ raw_user_meta_data: Record<string, unknown> }>(
        "select raw_user_meta_data from auth.users where id = $1",
        [outro],
      )).rows[0].raw_user_meta_data;
    assert.equal(metadata.cadastro_radar, undefined);
    const feedback = () =>
      db.query(
        "insert into eventos_produto(nome,origem,user_id,perfil_id) values ('vaga_util','telegram',$1,$2)",
        [dono, saved.id],
      );
    await assert.rejects(feedback);
    await db.query(
      "update perfis set telegram_chat_id = '123' where user_id = $1",
      [dono],
    );
    await feedback();
    await db.query("update perfis set ativo = false where user_id = $1", [
      dono,
    ]);
    await assert.rejects(feedback);
    await db.query("update perfis set ativo = true where user_id = $1", [dono]);
    await db.query("select set_config('request.jwt.claim.sub', $1, false)", [
      dono,
    ]);
    await db.exec("set role authenticated");
    assert.equal(await count("perfis"), 1);
    await assert.rejects(() => db.exec("select * from cadastros_pendentes"));
    await assert.rejects(() =>
      db.exec("update perfis set versao_dos_termos = 'forjada'")
    );
    await assert.rejects(() =>
      db.exec("update perfis set termos_aceitos_em = now()")
    );
    await assert.rejects(() =>
      db.query(
        "insert into perfis(user_id,curso,periodo,habilidades,cidade,modalidade) values ($1,'Curso',1,'{Python}','Cidade','remoto')",
        [dono],
      )
    );
    await db.exec("update perfis set aceita_emails = true");
    const download = (await db.query<
      {
        dados: {
          conta: { email: string };
          perfil: { aceita_emails: boolean; token_vinculo?: string };
        };
      }
    >("select baixar_meus_dados() dados")).rows[0].dados;
    assert.equal(download.conta.email, "dono@example.com");
    assert.equal(download.perfil.aceita_emails, true);
    assert.equal(download.perfil.token_vinculo, undefined);
    assert.ok(!JSON.stringify(download).includes("Cidade privada"));
    await db.exec("select excluir_minha_conta()");
    const changed = await db.query(
      "update perfis set aceita_emails = false returning id",
    );
    assert.equal(changed.rows.length, 0);
    await db.exec("reset role");
    await assert.rejects(feedback);
    for (
      const invalid of [
        { ...cadastro, aceitou_termos: false },
        { ...cadastro, sessao_id: "inválida" },
        { ...cadastro, perfil: { ...cadastro.perfil, habilidades: [123] } },
        {
          ...cadastro,
          perfil: { ...cadastro.perfil, areas_de_interesse: ["inventada"] },
        },
        { ...cadastro, perfil: { ...cadastro.perfil, periodo: "3.5" } },
      ]
    ) {
      await assert.rejects(() =>
        db.query("select validar_cadastro_radar($1)", [invalid])
      );
    }
    const versaoNova = (await db.query<{ versao_dos_termos: string }>(
      "select versao_dos_termos from perfis where user_id = $1",
      [outro],
    )).rows[0].versao_dos_termos;
    assert.equal(versaoNova, "2026-09-06");
    for (const versao of ["", "qualquer", "2026-02-31", 20260905, null]) {
      await assert.rejects(() =>
        db.query("select validar_cadastro_radar($1)", [{
          ...cadastro,
          versao_dos_termos: versao,
        }])
      );
    }
    await db.exec("set role anon");
    await assert.rejects(() => db.exec("select baixar_meus_dados()"));
    await assert.rejects(() =>
      db.query("select concluir_meu_cadastro($1)", [cadastro])
    );
  } finally {
    await db.close();
  }
});
