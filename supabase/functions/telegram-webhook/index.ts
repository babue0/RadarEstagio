import { createClient } from "jsr:@supabase/supabase-js@2";
import {
  type AtualizacaoDoTelegram,
  chatIdDaMensagem,
  extrairPedidoDeVinculo,
  RESPOSTA_SEM_TOKEN,
  RESPOSTAS_DO_VINCULO,
  type ResultadoDoVinculo,
} from "./vinculo.ts";
import {
  ACAO_DE_RECUSA,
  ACAO_SEM_RECUSA,
  AVISO_DE_CONSULTA_DESCONHECIDA,
  AVISO_DE_RECUSA_REGISTRADA,
  AVISO_DE_TUDO_CERTO,
  type BotaoDoTeclado,
  type ConsultaDeFeedback,
  eMotivo,
  extrairClique,
  tecladoDeMotivos,
  tecladoSemONumeroRespondido,
} from "./feedback.ts";

const CABECALHO_DO_SEGREDO = "x-telegram-bot-api-secret-token";
const CODIGO_DE_VALOR_DUPLICADO = "23505";

const tokenDoBot = Deno.env.get("TELEGRAM_BOT_TOKEN")!;
const segredoDoWebhook = Deno.env.get("TELEGRAM_WEBHOOK_SECRET")!;
const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

async function responderNoTelegram(
  chatId: string,
  texto: string,
): Promise<void> {
  await fetch(`https://api.telegram.org/bot${tokenDoBot}/sendMessage`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, text: texto }),
  });
}

async function vincularChat(
  token: string,
  chatId: string,
): Promise<ResultadoDoVinculo> {
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
  return (await chatJaVinculado(chatId))
    ? "chat_ja_vinculado"
    : "token_ja_usado";
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

async function tratarAtualizacao(
  atualizacao: AtualizacaoDoTelegram,
): Promise<void> {
  const pedido = extrairPedidoDeVinculo(atualizacao);
  if (!pedido) {
    const chatId = chatIdDaMensagem(atualizacao);
    if (chatId) await responderNoTelegram(chatId, RESPOSTA_SEM_TOKEN);
    return;
  }
  const resultado = await vincularChat(pedido.token, pedido.chatId);
  await responderNoTelegram(pedido.chatId, RESPOSTAS_DO_VINCULO[resultado]);
}

interface EnvioDoToken {
  perfilId: string;
  userId: string;
  vagaId: number;
}

async function chamarTelegram(metodo: string, corpo: unknown): Promise<void> {
  await fetch(`https://api.telegram.org/bot${tokenDoBot}/${metodo}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(corpo),
  });
}

async function envioDoToken(token: string): Promise<EnvioDoToken | null> {
  const { data, error } = await supabase
    .from("envios")
    .select("perfil_id, vaga_id, perfis (user_id)")
    .eq("token", token)
    .maybeSingle();
  if (error) throw error;
  if (!data) return null;
  const perfil = data.perfis as unknown as { user_id: string } | null;
  if (!perfil) return null;
  return {
    perfilId: data.perfil_id,
    userId: perfil.user_id,
    vagaId: data.vaga_id,
  };
}

async function registrarRecusa(
  envio: EnvioDoToken,
  motivo: string,
): Promise<void> {
  const { error } = await supabase.from("eventos_produto").insert({
    nome: "vaga_irrelevante",
    origem: "telegram",
    user_id: envio.userId,
    perfil_id: envio.perfilId,
    vaga_id: envio.vagaId,
    propriedades: { motivo },
  });
  if (error) throw error;
}

async function perguntarOMotivo(consulta: ConsultaDeFeedback): Promise<void> {
  await chamarTelegram("editMessageReplyMarkup", {
    chat_id: consulta.chatId,
    message_id: consulta.mensagemId,
    reply_markup: { inline_keyboard: tecladoDeMotivos(consulta.token) },
  });
}

async function encerrarPergunta(consulta: ConsultaDeFeedback): Promise<void> {
  await chamarTelegram("deleteMessage", {
    chat_id: consulta.chatId,
    message_id: consulta.mensagemId,
  });
}

async function voltarAosNumeros(
  consulta: ConsultaDeFeedback,
  teclado: BotaoDoTeclado[][],
): Promise<void> {
  const restante = tecladoSemONumeroRespondido(teclado, consulta.token);
  if (restante.length === 0) {
    await encerrarPergunta(consulta);
    return;
  }
  await chamarTelegram("editMessageReplyMarkup", {
    chat_id: consulta.chatId,
    message_id: consulta.mensagemId,
    reply_markup: { inline_keyboard: restante },
  });
}

async function tratarClique(
  consulta: ConsultaDeFeedback,
  teclado: BotaoDoTeclado[][],
): Promise<string> {
  if (consulta.acao === ACAO_DE_RECUSA) {
    await perguntarOMotivo(consulta);
    return "";
  }
  if (consulta.acao === ACAO_SEM_RECUSA) {
    await encerrarPergunta(consulta);
    return AVISO_DE_TUDO_CERTO;
  }
  if (!eMotivo(consulta.acao)) return AVISO_DE_CONSULTA_DESCONHECIDA;
  const envio = await envioDoToken(consulta.token);
  if (!envio) return AVISO_DE_CONSULTA_DESCONHECIDA;
  await registrarRecusa(envio, consulta.acao);
  await voltarAosNumeros(consulta, teclado);
  return AVISO_DE_RECUSA_REGISTRADA;
}

Deno.serve(async (requisicao) => {
  if (requisicao.method !== "POST") return new Response(null, { status: 405 });
  if (requisicao.headers.get(CABECALHO_DO_SEGREDO) !== segredoDoWebhook) {
    return new Response(null, { status: 401 });
  }
  const atualizacao = await requisicao.json();
  const consulta = extrairClique(atualizacao);
  if (consulta) {
    const teclado =
      (atualizacao.callback_query?.message?.reply_markup?.inline_keyboard ??
        []) as BotaoDoTeclado[][];
    try {
      const aviso = await tratarClique(consulta, teclado);
      await chamarTelegram("answerCallbackQuery", {
        callback_query_id: consulta.id,
        text: aviso || undefined,
      });
    } catch (erro) {
      console.error("falha ao tratar clique do telegram", erro);
      return new Response(null, { status: 500 });
    }
    return new Response(null, { status: 200 });
  }
  try {
    await tratarAtualizacao(atualizacao);
  } catch (erro) {
    console.error("falha ao tratar atualização do telegram", erro);
  }
  return new Response(null, { status: 200 });
});
