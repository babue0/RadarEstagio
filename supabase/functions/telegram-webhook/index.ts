import { createClient } from "jsr:@supabase/supabase-js@2";
import {
  type Acao,
  type CliqueNoFeedback,
  ehMotivo,
  extrairCliqueNoFeedback,
  NOMES_DOS_EVENTOS,
  RESPOSTA_RECOMENDACAO_DESCONHECIDA,
  RESPOSTAS,
  tecladoDepoisDoClique,
} from "./feedback.ts";
import {
  type AtualizacaoDoTelegram,
  chatIdDaMensagem,
  extrairPedidoDeVinculo,
  RESPOSTA_SEM_TOKEN,
  RESPOSTAS_DO_VINCULO,
  type ResultadoDoVinculo,
} from "./vinculo.ts";

interface EnvioDoFeedback {
  perfilId: string;
  vagaId: number;
}

const CABECALHO_DO_SEGREDO = "x-telegram-bot-api-secret-token";
const CODIGO_DE_VALOR_DUPLICADO = "23505";

const tokenDoBot = Deno.env.get("TELEGRAM_BOT_TOKEN")!;
const segredoDoWebhook = Deno.env.get("TELEGRAM_WEBHOOK_SECRET")!;
const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

async function chamarTelegram(metodo: string, corpo: Record<string, unknown>): Promise<void> {
  await fetch(`https://api.telegram.org/bot${tokenDoBot}/${metodo}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(corpo),
  });
}

async function responderNoTelegram(chatId: string, texto: string): Promise<void> {
  await chamarTelegram("sendMessage", { chat_id: chatId, text: texto });
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

async function envioDoClique(clique: CliqueNoFeedback): Promise<EnvioDoFeedback | null> {
  const { data, error } = await supabase
    .from("envios")
    .select("perfil_id, vaga_id, perfis (telegram_chat_id)")
    .eq("token", clique.token)
    .maybeSingle();
  if (error) throw error;
  const perfil = data?.perfis as unknown as { telegram_chat_id: string } | null;
  if (!data || perfil?.telegram_chat_id !== clique.chatId) return null;
  return { perfilId: data.perfil_id, vagaId: data.vaga_id };
}

async function registrarEvento(
  envio: EnvioDoFeedback,
  nome: string,
  propriedades: Record<string, string> = {},
): Promise<void> {
  const { error } = await supabase.from("eventos_produto").insert({
    nome,
    origem: "telegram",
    perfil_id: envio.perfilId,
    vaga_id: envio.vagaId,
    propriedades,
  });
  if (error) throw error;
}

async function registrarMotivoDaRecusa(envio: EnvioDoFeedback, motivo: string): Promise<void> {
  const { data, error } = await supabase
    .from("eventos_produto")
    .select("id")
    .eq("perfil_id", envio.perfilId)
    .eq("vaga_id", envio.vagaId)
    .eq("nome", "vaga_irrelevante")
    .order("id", { ascending: false })
    .limit(1)
    .maybeSingle();
  if (error) throw error;
  if (!data) {
    await registrarEvento(envio, "vaga_irrelevante", { motivo });
    return;
  }
  const recusa = await supabase
    .from("eventos_produto")
    .update({ propriedades: { motivo } })
    .eq("id", data.id);
  if (recusa.error) throw recusa.error;
}

async function anotarClique(envio: EnvioDoFeedback, acao: Acao): Promise<void> {
  if (ehMotivo(acao)) {
    await registrarMotivoDaRecusa(envio, acao);
    return;
  }
  await registrarEvento(envio, NOMES_DOS_EVENTOS[acao]);
}

async function tratarClique(clique: CliqueNoFeedback): Promise<void> {
  const envio = await envioDoClique(clique);
  if (!envio) {
    await chamarTelegram("answerCallbackQuery", {
      callback_query_id: clique.callbackId,
      text: RESPOSTA_RECOMENDACAO_DESCONHECIDA,
    });
    return;
  }
  await anotarClique(envio, clique.acao);
  await chamarTelegram("editMessageReplyMarkup", {
    chat_id: clique.chatId,
    message_id: clique.mensagemId,
    reply_markup: { inline_keyboard: tecladoDepoisDoClique(clique.acao, clique.token) },
  });
  await chamarTelegram("answerCallbackQuery", {
    callback_query_id: clique.callbackId,
    text: RESPOSTAS[clique.acao],
  });
}

async function tratarAtualizacao(atualizacao: AtualizacaoDoTelegram): Promise<void> {
  const clique = extrairCliqueNoFeedback(atualizacao);
  if (clique) {
    await tratarClique(clique);
    return;
  }
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
