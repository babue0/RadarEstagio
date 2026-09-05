import { type PerfilDoDestinatario, podeProcessarInteracao } from "../_shared/privacidade.ts";

export interface EnvioDaVaga {
  perfilId: string;
  userId: string;
  vagaId: number;
  url: string;
  perfil: PerfilDoDestinatario;
}

export async function destinoDoEnvio(
  envio: EnvioDaVaga | null,
  landing: string,
  registrar: boolean,
  registrarAbertura: (envio: EnvioDaVaga) => Promise<void>,
): Promise<string> {
  if (!envio || envio.perfil.excluida_em) return landing;
  if (registrar && podeProcessarInteracao(envio.perfil)) {
    try {
      await registrarAbertura(envio);
    } catch (erro) {
      console.error("vaga_aberta não foi registrada", erro);
    }
  }
  return envio.url;
}
