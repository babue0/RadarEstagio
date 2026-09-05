export interface PerfilDoDestinatario {
  user_id: string;
  ativo: boolean;
  excluida_em: string | null;
  telegram_chat_id: string | null;
}

export function podeProcessarInteracao(
  perfil: PerfilDoDestinatario | null,
  chatId?: string,
): boolean {
  return Boolean(
    perfil?.ativo && !perfil.excluida_em && perfil.telegram_chat_id &&
      (chatId === undefined || perfil.telegram_chat_id === chatId),
  );
}
