import { createClient } from "jsr:@supabase/supabase-js@2";
import {
  type AtualizacaoDoTelegram,
  chatIdDaMensagem,
  extrairPedidoDeVinculo,
  RESPOSTA_SEM_TOKEN,
  RESPOSTAS_DO_VINCULO,
  type ResultadoDoVinculo,
} from "./vinculo.ts";

const CABECALHO_DO_SEGREDO = "x-telegram-bot-api-secret-token";
const CODIGO_DE_VALOR_DUPLICADO = "23505";

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

async function vincularChat(token: string, chatId: string): Promise<ResultadoDoVinculo> {
  const { data, error } = await supabase
    .from("perfis")
    .update({
      telegram_chat_id: chatId,
      token_vinculo: crypto.randomUUID(),
      atualizado_em: new Date().toISOString(),
    })
    .eq("token_vinculo", token)
    .select("id");
  if (error?.code === CODIGO_DE_VALOR_DUPLICADO) return "chat_de_outra_conta";
  if (error) throw error;
  if (data.length === 1) return "vinculado";
  return (await chatJaVinculado(chatId)) ? "chat_ja_vinculado" : "token_ja_usado";
}

async function chatJaVinculado(chatId: string): Promise<boolean> {
  const { data, error } = await supabase
    .from("perfis")
    .select("id")
    .eq("telegram_chat_id", chatId)
    .maybeSingle();
  if (error) throw error;
  return data !== null;
}

async function tratarAtualizacao(atualizacao: AtualizacaoDoTelegram): Promise<void> {
  const pedido = extrairPedidoDeVinculo(atualizacao);
  if (!pedido) {
    const chatId = chatIdDaMensagem(atualizacao);
    if (chatId) await responderNoTelegram(chatId, RESPOSTA_SEM_TOKEN);
    return;
  }
  const resultado = await vincularChat(pedido.token, pedido.chatId);
  await responderNoTelegram(pedido.chatId, RESPOSTAS_DO_VINCULO[resultado]);
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
