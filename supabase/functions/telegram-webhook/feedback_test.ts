import { assertEquals } from "jsr:@std/assert@1";
import {
  ACAO_DE_RECUSA,
  ACAO_SEM_RECUSA,
  eMotivo,
  extrairClique,
  ROTULOS_DE_MOTIVO,
  tecladoDeMotivos,
  tecladoSemONumeroRespondido,
} from "./feedback.ts";

const TOKEN = "15130004-9e8c-4247-aa2d-0514b82d078e";
const OUTRO_TOKEN = "25130004-9e8c-4247-aa2d-0514b82d078e";

function clique(dados: string) {
  return {
    callback_query: {
      id: "clique-1",
      data: dados,
      message: { message_id: 77, chat: { id: 123 } },
    },
  };
}

function tecladoDeNumeros(...tokens: string[]) {
  return [
    tokens.map((token, indice) => ({
      text: String(indice + 1),
      callback_data: `${ACAO_DE_RECUSA}:${token}`,
    })),
    [{
      text: "Todas serviram",
      callback_data: `${ACAO_SEM_RECUSA}:${tokens[0]}`,
    }],
  ];
}

Deno.test("le a acao e o token do clique", () => {
  const consulta = extrairClique(clique(`${ACAO_DE_RECUSA}:${TOKEN}`));

  assertEquals(consulta?.acao, ACAO_DE_RECUSA);
  assertEquals(consulta?.token, TOKEN);
  assertEquals(consulta?.chatId, "123");
  assertEquals(consulta?.mensagemId, 77);
});

Deno.test("clique sem mensagem ou com dados fora do formato e ignorado", () => {
  assertEquals(
    extrairClique({
      callback_query: { id: "x", data: `${ACAO_DE_RECUSA}:${TOKEN}` },
    }),
    null,
  );
  assertEquals(extrairClique(clique("recusa:nao-e-uuid")), null);
  assertEquals(extrairClique(clique("")), null);
  assertEquals(extrairClique({}), null);
});

Deno.test("todo motivo do catalogo e reconhecido e nenhum outro", () => {
  for (const motivo of Object.keys(ROTULOS_DE_MOTIVO)) {
    assertEquals(eMotivo(motivo), true);
  }
  assertEquals(eMotivo(ACAO_DE_RECUSA), false);
  assertEquals(eMotivo("motivo_inventado"), false);
});

Deno.test("o teclado de motivos carrega o token e cabe no limite do telegram", () => {
  const linhas = tecladoDeMotivos(TOKEN);

  assertEquals(linhas.length, Object.keys(ROTULOS_DE_MOTIVO).length);
  for (const [botao] of linhas) {
    assertEquals(botao.callback_data.endsWith(`:${TOKEN}`), true);
    assertEquals(botao.callback_data.length <= 64, true);
  }
});

Deno.test("o numero respondido sai do teclado e os outros ficam", () => {
  const restante = tecladoSemONumeroRespondido(
    tecladoDeNumeros(TOKEN, OUTRO_TOKEN),
    TOKEN,
  );

  const dados = restante.flat().map((botao) => botao.callback_data);
  assertEquals(dados.includes(`${ACAO_DE_RECUSA}:${TOKEN}`), false);
  assertEquals(dados.includes(`${ACAO_DE_RECUSA}:${OUTRO_TOKEN}`), true);
});

Deno.test("responder o ultimo numero esvazia o teclado para a pergunta ser apagada", () => {
  const restante = tecladoSemONumeroRespondido(tecladoDeNumeros(TOKEN), TOKEN);

  assertEquals(restante, []);
});
