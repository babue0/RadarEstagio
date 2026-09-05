import { assertEquals } from "jsr:@std/assert@1";
import { dentroDaJanelaDoDiario } from "./entrega_imediata.ts";

Deno.test("janela do diario cobre 06:23 a 07:23 de brasilia", () => {
  assertEquals(dentroDaJanelaDoDiario(new Date("2026-09-05T09:23:00Z")), true);
  assertEquals(dentroDaJanelaDoDiario(new Date("2026-09-05T10:22:59Z")), true);
});

Deno.test("fora da janela a entrega imediata e liberada", () => {
  assertEquals(dentroDaJanelaDoDiario(new Date("2026-09-05T09:22:59Z")), false);
  assertEquals(dentroDaJanelaDoDiario(new Date("2026-09-05T10:23:00Z")), false);
  assertEquals(dentroDaJanelaDoDiario(new Date("2026-09-05T23:59:00Z")), false);
});
