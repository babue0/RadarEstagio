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

export const RESPOSTA_VINCULADO =
  "Telegram vinculado! Você vai receber as vagas compatíveis com o seu perfil todos os dias.";
export const RESPOSTA_TOKEN_INVALIDO =
  "Link inválido. Abra o site do Radar de Estágio e clique de novo em vincular o Telegram.";
export const RESPOSTA_SEM_TOKEN =
  "Para vincular, use o botão do Telegram no site do Radar de Estágio.";

export function extrairPedidoDeVinculo(
  atualizacao: AtualizacaoDoTelegram,
): PedidoDeVinculo | null {
  const mensagem = atualizacao.message;
  if (!mensagem?.text) return null;
  const encontrado = FORMATO_DO_TOKEN.exec(mensagem.text);
  if (!encontrado) return null;
  return { chatId: String(mensagem.chat.id), token: encontrado[1].toLowerCase() };
}

export function chatIdDaMensagem(atualizacao: AtualizacaoDoTelegram): string | null {
  const id = atualizacao.message?.chat.id;
  return id === undefined ? null : String(id);
}
