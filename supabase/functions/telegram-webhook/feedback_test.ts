import { assert, assertEquals } from "jsr:@std/assert@1";
import {
  extrairCliqueNoFeedback,
  MOTIVOS_DE_RECUSA,
  NOMES_DOS_EVENTOS,
  tecladoDepoisDoClique,
} from "./feedback.ts";

const TOKEN = "3f2504e0-4f89-11d3-9a0c-0305e82c3301";
const LIMITE_DO_CALLBACK_DATA = 64;

function clique(dado: string) {
  return {
    callback_query: {
      id: "42",
      data: dado,
      message: { message_id: 7, chat: { id: 123456 } },
    },
  };
}

Deno.test("extrai ação, token, chat e mensagem do clique", () => {
  assertEquals(extrairCliqueNoFeedback(clique(`util:${TOKEN}`)), {
    callbackId: "42",
    chatId: "123456",
    mensagemId: 7,
    acao: "util",
    token: TOKEN,
  });
});

Deno.test("aceita as três ações da mensagem e os quatro motivos", () => {
  const acoes = ["util", "irrelevante", "candidatura", ...MOTIVOS_DE_RECUSA.map((m) => m.acao)];

  for (const acao of acoes) {
    assertEquals(extrairCliqueNoFeedback(clique(`${acao}:${TOKEN}`))?.acao, acao);
  }
});

Deno.test("ignora ação desconhecida, token inválido e atualização sem clique", () => {
  assertEquals(extrairCliqueNoFeedback(clique(`apagar:${TOKEN}`)), null);
  assertEquals(extrairCliqueNoFeedback(clique("util:nao-e-uuid")), null);
  assertEquals(extrairCliqueNoFeedback({}), null);
});

Deno.test("todo callback_data cabe no limite de 64 bytes do Telegram", () => {
  const acoes = ["util", "irrelevante", "candidatura", ...MOTIVOS_DE_RECUSA.map((m) => m.acao)];

  for (const acao of acoes) {
    const dado = `${acao}:${TOKEN}`;
    assert(new TextEncoder().encode(dado).length <= LIMITE_DO_CALLBACK_DATA, dado);
  }
});

Deno.test("o polegar para baixo troca os botões pelos quatro motivos", () => {
  const teclado = tecladoDepoisDoClique("irrelevante", TOKEN);

  assertEquals(teclado.length, MOTIVOS_DE_RECUSA.length);
  assertEquals(teclado[0][0].callback_data, `motivo_area:${TOKEN}`);
  assertEquals(teclado[3][0].text, "Já vi / vaga velha");
});

Deno.test("o polegar para cima deixa só a candidatura", () => {
  const teclado = tecladoDepoisDoClique("util", TOKEN);

  assertEquals(teclado, [[{ text: "Candidatei-me", callback_data: `candidatura:${TOKEN}` }]]);
});

Deno.test("motivo e candidatura encerram os botões daquela vaga", () => {
  assertEquals(tecladoDepoisDoClique("motivo_area", TOKEN), []);
  assertEquals(tecladoDepoisDoClique("candidatura", TOKEN), []);
});

Deno.test("cada ação da mensagem tem um evento do catálogo", () => {
  assertEquals(NOMES_DOS_EVENTOS, {
    util: "vaga_util",
    irrelevante: "vaga_irrelevante",
    candidatura: "candidatura_iniciada",
  });
});
