import { createClient } from "jsr:@supabase/supabase-js@2";
import { redirecionarPara, tokenDaRequisicao } from "./redirecionamento.ts";

interface EnvioDaVaga {
  perfilId: string;
  vagaId: number;
  url: string;
}

const urlDaLanding = Deno.env.get("URL_DA_LANDING")!;
const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

async function envioDoToken(token: string): Promise<EnvioDaVaga | null> {
  const { data, error } = await supabase
    .from("envios")
    .select("perfil_id, vaga_id, vagas (url)")
    .eq("token", token)
    .maybeSingle();
  if (error) throw error;
  if (!data) return null;
  const vaga = data.vagas as unknown as { url: string } | null;
  if (!vaga) return null;
  return { perfilId: data.perfil_id, vagaId: data.vaga_id, url: vaga.url };
}

async function registrarVagaAberta(envio: EnvioDaVaga): Promise<void> {
  const { error } = await supabase.from("eventos_produto").insert({
    nome: "vaga_aberta",
    origem: "telegram",
    perfil_id: envio.perfilId,
    vaga_id: envio.vagaId,
  });
  if (error) throw error;
}

async function destinoDoToken(url: string): Promise<string> {
  const token = tokenDaRequisicao(url);
  if (!token) return urlDaLanding;
  const envio = await envioDoToken(token);
  if (!envio) return urlDaLanding;
  try {
    await registrarVagaAberta(envio);
  } catch (erro) {
    console.error("vaga_aberta não foi registrada", erro);
  }
  return envio.url;
}

Deno.serve(async (requisicao) => {
  if (requisicao.method !== "GET" && requisicao.method !== "HEAD") {
    return new Response(null, { status: 405 });
  }
  try {
    return redirecionarPara(await destinoDoToken(requisicao.url));
  } catch (erro) {
    console.error("falha ao redirecionar para a vaga", erro);
    return redirecionarPara(urlDaLanding);
  }
});
