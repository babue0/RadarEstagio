const REPOSITORIO = "babue0/RadarEstagio";
const WORKFLOW = "radar-diario.yml";
const INICIO_DA_JANELA_DO_DIARIO_EM_MINUTOS_UTC = 9 * 60 + 23;
const FIM_DA_JANELA_DO_DIARIO_EM_MINUTOS_UTC = 10 * 60 + 23;

export function dentroDaJanelaDoDiario(agora: Date): boolean {
  const minutos = agora.getUTCHours() * 60 + agora.getUTCMinutes();
  return minutos >= INICIO_DA_JANELA_DO_DIARIO_EM_MINUTOS_UTC &&
    minutos < FIM_DA_JANELA_DO_DIARIO_EM_MINUTOS_UTC;
}

export async function dispararEntregaImediata(
  perfilId: string,
  agora: Date = new Date(),
): Promise<void> {
  if (dentroDaJanelaDoDiario(agora)) return;
  const token = Deno.env.get("GITHUB_DISPATCH_TOKEN");
  if (!token) {
    console.warn(
      "GITHUB_DISPATCH_TOKEN ausente: a primeira busca fica para o diário",
    );
    return;
  }
  try {
    const resposta = await fetch(
      `https://api.github.com/repos/${REPOSITORIO}/actions/workflows/${WORKFLOW}/dispatches`,
      {
        method: "POST",
        headers: {
          authorization: `Bearer ${token}`,
          accept: "application/vnd.github+json",
          "content-type": "application/json",
        },
        body: JSON.stringify({ ref: "main", inputs: { perfil: perfilId } }),
      },
    );
    if (!resposta.ok) {
      console.error(`disparo da primeira busca falhou: HTTP ${resposta.status}`);
    }
  } catch (erro) {
    console.error("disparo da primeira busca falhou", erro);
  }
}
