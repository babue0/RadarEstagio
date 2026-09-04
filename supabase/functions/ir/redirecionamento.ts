const FORMATO_DO_TOKEN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

const PARAMETRO_DO_TOKEN = "t";

export function tokenDaRequisicao(url: string): string | null {
  const valor = new URL(url).searchParams.get(PARAMETRO_DO_TOKEN);
  if (!valor || !FORMATO_DO_TOKEN.test(valor)) return null;
  return valor.toLowerCase();
}

export function redirecionarPara(destino: string): Response {
  return new Response(null, {
    status: 302,
    headers: { location: destino, "cache-control": "no-store" },
  });
}
