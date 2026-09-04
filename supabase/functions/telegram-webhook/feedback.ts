import { type AtualizacaoDoTelegram } from "./vinculo.ts";

const FORMATO_DO_DADO =
  /^([a-z_]{1,16}):([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$/i;

export const ACOES_DE_FEEDBACK = ["util", "irrelevante", "candidatura"] as const;
export const MOTIVOS_DE_RECUSA = [
  { acao: "motivo_area", rotulo: "Não é da minha área" },
  { acao: "motivo_exigencia", rotulo: "Pedem demais para estágio" },
  { acao: "motivo_logistica", rotulo: "Local ou modalidade" },
  { acao: "motivo_repetida", rotulo: "Já vi / vaga velha" },
] as const;

export type AcaoDeFeedback = typeof ACOES_DE_FEEDBACK[number];
export type AcaoDeMotivo = typeof MOTIVOS_DE_RECUSA[number]["acao"];
export type Acao = AcaoDeFeedback | AcaoDeMotivo;

export interface BotaoInline {
  text: string;
  callback_data: string;
}

export interface CliqueNoFeedback {
  callbackId: string;
  chatId: string;
  mensagemId: number;
  acao: Acao;
  token: string;
}

export const NOMES_DOS_EVENTOS: Record<AcaoDeFeedback, string> = {
  util: "vaga_util",
  irrelevante: "vaga_irrelevante",
  candidatura: "candidatura_iniciada",
};

export const RESPOSTAS: Record<Acao, string> = {
  util: "Anotado — isso ajuda a calibrar as próximas.",
  irrelevante: "Por que não serve? Escolha um motivo.",
  candidatura: "Boa sorte! Candidatura registrada.",
  motivo_area: "Obrigado, motivo registrado.",
  motivo_exigencia: "Obrigado, motivo registrado.",
  motivo_logistica: "Obrigado, motivo registrado.",
  motivo_repetida: "Obrigado, motivo registrado.",
};

export const RESPOSTA_RECOMENDACAO_DESCONHECIDA =
  "Não encontrei essa recomendação. Ela pode ser de antes do vínculo atual.";

export function extrairCliqueNoFeedback(
  atualizacao: AtualizacaoDoTelegram,
): CliqueNoFeedback | null {
  const clique = atualizacao.callback_query;
  if (!clique?.id || !clique.data || !clique.message) return null;
  const encontrado = FORMATO_DO_DADO.exec(clique.data);
  if (!encontrado) return null;
  const acao = encontrado[1].toLowerCase();
  if (!ehAcaoConhecida(acao)) return null;
  return {
    callbackId: clique.id,
    chatId: String(clique.message.chat.id),
    mensagemId: clique.message.message_id,
    acao,
    token: encontrado[2].toLowerCase(),
  };
}

export function ehAcaoConhecida(acao: string): acao is Acao {
  return ehMotivo(acao) || (ACOES_DE_FEEDBACK as readonly string[]).includes(acao);
}

export function ehMotivo(acao: string): acao is AcaoDeMotivo {
  return MOTIVOS_DE_RECUSA.some((motivo) => motivo.acao === acao);
}

export function tecladoDepoisDoClique(acao: Acao, token: string): BotaoInline[][] {
  if (acao === "irrelevante") {
    return MOTIVOS_DE_RECUSA.map((motivo) => [
      { text: motivo.rotulo, callback_data: `${motivo.acao}:${token}` },
    ]);
  }
  if (acao === "util") {
    return [[{ text: "Candidatei-me", callback_data: `candidatura:${token}` }]];
  }
  return [];
}
