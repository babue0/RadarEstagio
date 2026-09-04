const FORMATO_DO_TOKEN =
  /^\/start\s+([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\s*$/i;

export interface MensagemDoTelegram {
  chat: { id: number };
  text?: string;
}

export interface AtualizacaoDoTelegram {
  message?: MensagemDoTelegram;
}

export interface PedidoDeVinculo {
  chatId: string;
  token: string;
}

export type ResultadoDoVinculo =
  | "vinculado"
  | "token_ja_usado"
  | "chat_de_outra_conta"
  | "chat_ja_vinculado";

export const RESPOSTA_VINCULADO =
  "Telegram vinculado! Você vai receber as vagas compatíveis com o seu perfil todos os dias de manhã.";
export const RESPOSTA_TOKEN_JA_USADO =
  "Este link já foi usado ou expirou. Abra o site do Radar de Estágio e clique de novo em vincular o Telegram.";
export const RESPOSTA_CHAT_DE_OUTRA_CONTA =
  "Este Telegram já está vinculado a outra conta do Radar de Estágio.";
export const RESPOSTA_CHAT_JA_VINCULADO =
  "Seu Telegram já está vinculado. Nada a fazer: as vagas chegam aqui todos os dias de manhã.";
export const RESPOSTA_SEM_TOKEN =
  "Para vincular, use o botão do Telegram no site do Radar de Estágio.";

export const RESPOSTAS_DO_VINCULO: Record<ResultadoDoVinculo, string> = {
  vinculado: RESPOSTA_VINCULADO,
  token_ja_usado: RESPOSTA_TOKEN_JA_USADO,
  chat_de_outra_conta: RESPOSTA_CHAT_DE_OUTRA_CONTA,
  chat_ja_vinculado: RESPOSTA_CHAT_JA_VINCULADO,
};

export function extrairPedidoDeVinculo(
  atualizacao: AtualizacaoDoTelegram,
): PedidoDeVinculo | null {
  const mensagem = atualizacao.message;
  if (!mensagem?.text) return null;
  const encontrado = FORMATO_DO_TOKEN.exec(mensagem.text);
  if (!encontrado) return null;
  return {
    chatId: String(mensagem.chat.id),
    token: encontrado[1].toLowerCase(),
  };
}

export function chatIdDaMensagem(
  atualizacao: AtualizacaoDoTelegram,
): string | null {
  const id = atualizacao.message?.chat.id;
  return id === undefined ? null : String(id);
}
