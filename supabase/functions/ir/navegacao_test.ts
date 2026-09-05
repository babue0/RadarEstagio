import { destinoDoEnvio, type EnvioDaVaga } from "./navegacao.ts";
import { assertEquals } from "jsr:@std/assert";

const envio: EnvioDaVaga = {
  perfilId: "perfil",
  userId: "dono",
  vagaId: 1,
  url: "https://vaga.example/1",
  perfil: { user_id: "dono", ativo: true, excluida_em: null, telegram_chat_id: "123" },
};

Deno.test("pausa e desvínculo preservam a navegação sem registrar abertura", async () => {
  for (
    const perfil of [{ ...envio.perfil, ativo: false }, { ...envio.perfil, telegram_chat_id: null }]
  ) {
    let registros = 0;
    const destino = await destinoDoEnvio({ ...envio, perfil }, "landing", true, async () => {
      registros++;
    });
    assertEquals(destino, envio.url);
    assertEquals(registros, 0);
  }
});

Deno.test("exclusão e token inexistente bloqueiam navegação e registro", async () => {
  for (
    const candidato of [null, { ...envio, perfil: { ...envio.perfil, excluida_em: "2026-09-05" } }]
  ) {
    let registros = 0;
    assertEquals(
      await destinoDoEnvio(candidato, "landing", true, async () => {
        registros++;
      }),
      "landing",
    );
    assertEquals(registros, 0);
  }
});

Deno.test("conta ativa registra GET, mas HEAD só navega", async () => {
  let registros = 0;
  for (const registrar of [true, false]) {
    assertEquals(
      await destinoDoEnvio(envio, "landing", registrar, async () => {
        registros++;
      }),
      envio.url,
    );
  }
  assertEquals(registros, 1);
});
