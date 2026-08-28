import { createClient } from "jsr:@supabase/supabase-js@2";
import {
  type AtualizacaoDoTelegram,
  chatIdDaMensagem,
  extrairPedidoDeVinculo,
  RESPOSTA_SEM_TOKEN,
  RESPOSTA_TOKEN_INVALIDO,
  RESPOSTA_VINCULADO,
} from "./vinculo.ts";

const CABECALHO_DO_SEGREDO = "x-telegram-bot-api-secret-token";

const tokenDoBot = Deno.env.get("TELEGRAM_BOT_TOKEN")!;
const segredoDoWebhook = Deno.env.get("TELEGRAM_WEBHOOK_SECRET")!;
const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

async function responderNoTelegram(chatId: string, texto: string): Promise<void> {
  await fetch(`https://api.telegram.org/bot${tokenDoBot}/sendMessage`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, text: texto }),
  });
}

async function vincularChat(token: string, chatId: string): Promise<boolean> {
  const { data, error } = await supabase
    .from("perfis")
    .update({ telegram_chat_id: chatId, atualizado_em: new Date().toISOString() })
    .eq("token_vinculo", token)
    .select("id");
  if (error) throw error;
  return data.length === 1;
}

async function tratarAtualizacao(atualizacao: AtualizacaoDoTelegram): Promise<void> {
  const pedido = extrairPedidoDeVinculo(atualizacao);
  if (!pedido) {
    const chatId = chatIdDaMensagem(atualizacao);
    if (chatId) await responderNoTelegram(chatId, RESPOSTA_SEM_TOKEN);
    return;
  }
  const vinculado = await vincularChat(pedido.token, pedido.chatId);
  await responderNoTelegram(
    pedido.chatId,
    vinculado ? RESPOSTA_VINCULADO : RESPOSTA_TOKEN_INVALIDO,
  );
}

Deno.serve(async (requisicao) => {
  if (requisicao.method !== "POST") return new Response(null, { status: 405 });
  if (requisicao.headers.get(CABECALHO_DO_SEGREDO) !== segredoDoWebhook) {
    return new Response(null, { status: 401 });
  }
  try {
    await tratarAtualizacao(await requisicao.json());
  } catch (erro) {
    console.error("falha ao tratar atualização do telegram", erro);
  }
  return new Response(null, { status: 200 });
});
