import assert from "assert";
import { podeProcessarInteracao } from "../../supabase/functions/_shared/privacidade.ts";

Deno.test("interações antigas exigem conta ativa e o chat ainda vinculado", () => {
  const perfil = {
    user_id: "dono",
    ativo: true,
    excluida_em: null,
    telegram_chat_id: "123",
  };
  assert.equal(podeProcessarInteracao(perfil, "123"), true);
  assert.equal(podeProcessarInteracao(perfil), true);
  assert.equal(podeProcessarInteracao(perfil, "456"), false);
  assert.equal(podeProcessarInteracao(null), false);
  assert.equal(podeProcessarInteracao({ ...perfil, ativo: false }), false);
  assert.equal(
    podeProcessarInteracao({ ...perfil, excluida_em: "2026-09-05" }),
    false,
  );
  assert.equal(
    podeProcessarInteracao({ ...perfil, telegram_chat_id: null }),
    false,
  );
});
