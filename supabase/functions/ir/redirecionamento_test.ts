import { assertEquals } from "jsr:@std/assert@1";
import { redirecionarPara, tokenDaRequisicao } from "./redirecionamento.ts";

const TOKEN = "3f2504e0-4f89-11d3-9a0c-0305e82c3301";
const URL_DA_FUNCAO = "https://projeto.supabase.co/functions/v1/ir";

Deno.test("extrai o token do parâmetro t", () => {
  assertEquals(tokenDaRequisicao(`${URL_DA_FUNCAO}?t=${TOKEN}`), TOKEN);
});

Deno.test("normaliza token em maiúsculas", () => {
  assertEquals(
    tokenDaRequisicao(`${URL_DA_FUNCAO}?t=${TOKEN.toUpperCase()}`),
    TOKEN,
  );
});

Deno.test("ignora requisição sem token", () => {
  assertEquals(tokenDaRequisicao(URL_DA_FUNCAO), null);
});

Deno.test("ignora token que não é uuid", () => {
  assertEquals(tokenDaRequisicao(`${URL_DA_FUNCAO}?t=abc123`), null);
});

Deno.test("redireciona com 302 sem deixar o navegador guardar o destino", () => {
  const resposta = redirecionarPara("https://exemplo.com/vaga/1");

  assertEquals(resposta.status, 302);
  assertEquals(resposta.headers.get("location"), "https://exemplo.com/vaga/1");
  assertEquals(resposta.headers.get("cache-control"), "no-store");
});
