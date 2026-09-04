export type MotivoDaRecusa =
  | "motivo_area"
  | "motivo_exigencia"
  | "motivo_logistica"
  | "motivo_repetida";

export interface BotaoDoTeclado {
  text: string;
  callback_data: string;
}

export interface ConsultaDeFeedback {
  id: string;
  chatId: string;
  mensagemId: number;
  acao: string;
  token: string;
}

export interface CliqueDoTelegram {
  id: string;
  data?: string;
  message?: { message_id: number; chat: { id: number } };
}

const FORMATO_DO_CLIQUE =
  /^([a-z_]+):([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$/i;

export const ACAO_DE_RECUSA = "recusa";
export const ACAO_SEM_RECUSA = "todas";

export const ROTULOS_DE_MOTIVO: Record<MotivoDaRecusa, string> = {
  motivo_area: "Não é da minha área",
  motivo_exigencia: "Pedem demais",
  motivo_logistica: "Local ou modalidade",
  motivo_repetida: "Já vi essa",
};

export const AVISO_DE_RECUSA_REGISTRADA =
  "Obrigado, isso ajuda a melhorar as próximas.";
export const AVISO_DE_TUDO_CERTO = "Combinado, obrigado.";
export const AVISO_DE_CONSULTA_DESCONHECIDA = "Esta pergunta não vale mais.";

export function extrairClique(atualizacao: {
  callback_query?: CliqueDoTelegram;
}): ConsultaDeFeedback | null {
  const clique = atualizacao.callback_query;
  if (!clique?.data || !clique.message) return null;
  const encontrado = FORMATO_DO_CLIQUE.exec(clique.data);
  if (!encontrado) return null;
  return {
    id: clique.id,
    chatId: String(clique.message.chat.id),
    mensagemId: clique.message.message_id,
    acao: encontrado[1],
    token: encontrado[2].toLowerCase(),
  };
}

export function eMotivo(acao: string): acao is MotivoDaRecusa {
  return acao in ROTULOS_DE_MOTIVO;
}

export function tecladoDeMotivos(token: string): BotaoDoTeclado[][] {
  return (Object.keys(ROTULOS_DE_MOTIVO) as MotivoDaRecusa[]).map((motivo) => [
    { text: ROTULOS_DE_MOTIVO[motivo], callback_data: `${motivo}:${token}` },
  ]);
}

export function tecladoSemONumeroRespondido(
  linhas: BotaoDoTeclado[][],
  token: string,
): BotaoDoTeclado[][] {
  const restantes = linhas
    .map((linha) =>
      linha.filter((botao) => !botao.callback_data.endsWith(`:${token}`))
    )
    .filter((linha) => linha.length > 0);
  return restantes.filter((linha) =>
      linha.some((botao) =>
        botao.callback_data.startsWith(`${ACAO_DE_RECUSA}:`)
      )
    ).length > 0
    ? restantes
    : [];
}
