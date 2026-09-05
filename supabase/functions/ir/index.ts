import { createClient } from "jsr:@supabase/supabase-js@2";
import { redirecionarPara, tokenDaRequisicao } from "./redirecionamento.ts";
import {
  type PerfilDoDestinatario,
  podeProcessarInteracao,
} from "../_shared/privacidade.ts";

interface EnvioDaVaga {
  perfilId: string;
  userId: string;
  vagaId: number;
  url: string;
}

const urlDaLandingConfigurada = Deno.env.get("URL_DA_LANDING");
if (!urlDaLandingConfigurada) {
  throw new Error(
    "URL_DA_LANDING é obrigatória: sem ela o token inválido não tem para onde ir",
  );
}
const urlDaLanding: string = urlDaLandingConfigurada;
const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

async function envioDoToken(token: string): Promise<EnvioDaVaga | null> {
  const { data, error } = await supabase
    .from("envios")
    .select(
      "perfil_id, vaga_id, vagas (url), perfis (user_id, ativo, excluida_em, telegram_chat_id)",
    )
    .eq("token", token)
    .maybeSingle();
  if (error) throw error;
  if (!data) return null;
  const vaga = data.vagas as unknown as { url: string } | null;
  const perfil = data.perfis as unknown as PerfilDoDestinatario | null;
  if (!vaga || !perfil || !podeProcessarInteracao(perfil)) return null;
  return {
    perfilId: data.perfil_id,
    userId: perfil.user_id,
    vagaId: data.vaga_id,
    url: vaga.url,
  };
}

async function registrarVagaAberta(envio: EnvioDaVaga): Promise<void> {
  const { error } = await supabase.from("eventos_produto").insert({
    nome: "vaga_aberta",
    origem: "telegram",
    user_id: envio.userId,
    perfil_id: envio.perfilId,
    vaga_id: envio.vagaId,
  });
  if (error) throw error;
}

async function destinoDoToken(
  url: string,
  registrar: boolean,
): Promise<string> {
  const token = tokenDaRequisicao(url);
  if (!token) return urlDaLanding;
  const envio = await envioDoToken(token);
  if (!envio) return urlDaLanding;
  if (!registrar) return envio.url;
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
    const destino = await destinoDoToken(
      requisicao.url,
      requisicao.method === "GET",
    );
    return redirecionarPara(destino);
  } catch (erro) {
    console.error("falha ao redirecionar para a vaga", erro);
    return redirecionarPara(urlDaLanding);
  }
});
