import { assertEquals } from "jsr:@std/assert@1";
import { chatIdDaMensagem, extrairPedidoDeVinculo } from "./vinculo.ts";

const TOKEN = "3f2504e0-4f89-11d3-9a0c-0305e82c3301";

Deno.test("extrai token e chat_id de /start com token", () => {
  const pedido = extrairPedidoDeVinculo({
    message: { chat: { id: 123456 }, text: `/start ${TOKEN}` },
  });
  assertEquals(pedido, { chatId: "123456", token: TOKEN });
});

Deno.test("normaliza token em maiúsculas", () => {
  const pedido = extrairPedidoDeVinculo({
    message: { chat: { id: 1 }, text: `/start ${TOKEN.toUpperCase()}` },
  });
  assertEquals(pedido?.token, TOKEN);
});

Deno.test("ignora /start sem token", () => {
  assertEquals(extrairPedidoDeVinculo({ message: { chat: { id: 1 }, text: "/start" } }), null);
});

Deno.test("ignora token que não é uuid", () => {
  assertEquals(
    extrairPedidoDeVinculo({ message: { chat: { id: 1 }, text: "/start abc123" } }),
    null,
  );
});

Deno.test("ignora texto comum", () => {
  assertEquals(extrairPedidoDeVinculo({ message: { chat: { id: 1 }, text: "oi" } }), null);
});

Deno.test("ignora atualização sem mensagem", () => {
  assertEquals(extrairPedidoDeVinculo({}), null);
  assertEquals(chatIdDaMensagem({}), null);
});

Deno.test("devolve chat_id como texto", () => {
  assertEquals(chatIdDaMensagem({ message: { chat: { id: 987 } } }), "987");
});
