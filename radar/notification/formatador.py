from datetime import date
from html import escape
from urllib.parse import urlsplit

from radar.domain.models import Recomendacao, Vaga

LIMITE_DE_CARACTERES_DO_TELEGRAM = 4096
MAXIMO_DE_PONTOS_EXIBIDOS = 3
SEPARADOR_ENTRE_VAGAS = "\n\n───────────────\n\n"
PARAMETRO_DO_TOKEN = "t"
PREFIXO_DE_SUBDOMINIO_IGNORADO = "www."
ROTULOS_MODALIDADE = {
    "remoto": "Remoto",
    "presencial": "Presencial",
    "hibrido": "Híbrido",
    "indiferente": "Indiferente",
}


def formatar_mensagem(
    recomendacoes: list[Recomendacao], data: date, url_de_rastreio: str = ""
) -> str:
    ranqueadas = sorted(
        recomendacoes, key=lambda recomendacao: recomendacao.resultado.nota, reverse=True
    )
    blocos = [
        formatar_vaga(posicao, recomendacao, url_de_rastreio)
        for posicao, recomendacao in enumerate(ranqueadas, start=1)
    ]
    return cabecalho(data) + "\n\n" + SEPARADOR_ENTRE_VAGAS.join(blocos)


def formatar_mensagem_sem_vagas(data: date, dias_de_silencio: int | None = None) -> str:
    mensagem = (
        f"{cabecalho(data)}\n\n"
        "Nenhuma vaga nova compatível com o seu perfil hoje.\n"
        "O Radar volta a procurar amanhã de manhã."
    )
    if dias_de_silencio is None:
        return mensagem
    return (
        f"{mensagem}\n\n"
        f"Já são {dias_de_silencio} dias sem nenhuma recomendação. "
        "Perfis presenciais restritos a uma cidade recebem menos vagas do que perfis "
        "que também aceitam remoto ou híbrido."
    )


def cabecalho(data: date) -> str:
    return f"📡 <b>Radar de Estágio</b> — {data.strftime('%d/%m/%Y')}"


def formatar_resumo_da_execucao(
    data: date,
    usuarios: int,
    atendidos: int,
    vagas_enviadas: int,
    vagas_coletadas: int,
    requisicoes: int,
) -> str:
    return (
        f"🛠️ <b>Radar — execução de {data.strftime('%d/%m/%Y')}</b>\n"
        f"Usuários ativos: {usuarios}\n"
        f"Receberam recomendação: {atendidos}\n"
        f"Vagas enviadas: {vagas_enviadas}\n"
        f"Vagas coletadas: {vagas_coletadas}\n"
        f"Requisições ao avaliador: {requisicoes}"
    )


def formatar_falha_da_execucao(data: date, erro: str) -> str:
    return f"🛠️ <b>Radar — execução de {data.strftime('%d/%m/%Y')} falhou</b>\n{escape(erro)}"


def formatar_vaga(posicao: int, recomendacao: Recomendacao, url_de_rastreio: str = "") -> str:
    resultado = recomendacao.resultado
    vaga = resultado.vaga
    linhas = [
        f"<b>{posicao}. {escape(vaga.titulo)}</b> — {escape(vaga.empresa)}",
        f"📍 {escape(vaga.localizacao)} · {escape(rotulo_modalidade(vaga))}",
        f"🏷️ Fonte: {escape(rotulo_fonte(vaga.fonte))} · Publicada em {vaga.publicada_em:%d/%m/%Y}",
        f"⭐ <b>Nota {resultado.nota}/100</b>",
    ]
    if resultado.requisitos_atendidos:
        linhas.append(
            f"✅ <b>Requisitos atendidos:</b> {formatar_requisitos(resultado.requisitos_atendidos)}"
        )
    if resultado.requisitos_nao_atendidos:
        linhas.append(
            "❌ <b>Requisitos não atendidos:</b> "
            f"{formatar_requisitos(resultado.requisitos_nao_atendidos)}"
        )
    if (
        resultado.requisitos_tecnicos_analisados
        and vaga.descricao_completa
        and not resultado.requisitos_atendidos
        and not resultado.requisitos_nao_atendidos
    ):
        linhas.append("ℹ️ <b>Requisitos técnicos:</b> não informados na descrição")
    if resultado.pontos_a_favor:
        linhas.append(f"✅ {formatar_pontos(resultado.pontos_a_favor)}")
    if resultado.pontos_contra:
        linhas.append(f"❌ {formatar_pontos(resultado.pontos_contra)}")
    for aviso in resultado.avisos_objetivos:
        linhas.append(f"⚠️ {escape(aviso)}")
    if resultado.alerta_pegadinha:
        linhas.append(f"⚠️ {escape(resultado.alerta_pegadinha)}")
    destino = url_de_abertura(recomendacao, url_de_rastreio)
    linhas.append(f'🔗 <a href="{escape(destino)}">Ver vaga em {escape(dominio_da_vaga(vaga))}</a>')
    return "\n".join(linhas)


def url_de_abertura(recomendacao: Recomendacao, url_de_rastreio: str) -> str:
    if not url_de_rastreio:
        return recomendacao.resultado.vaga.url
    return f"{url_de_rastreio}?{PARAMETRO_DO_TOKEN}={recomendacao.token}"


def dominio_da_vaga(vaga: Vaga) -> str:
    dominio = urlsplit(vaga.url).hostname or vaga.fonte
    return dominio.removeprefix(PREFIXO_DE_SUBDOMINIO_IGNORADO)


def rotulo_modalidade(vaga: Vaga) -> str:
    if vaga.modalidade is None:
        return "Modalidade não informada"
    return ROTULOS_MODALIDADE[vaga.modalidade.value]


def rotulo_fonte(fonte: str) -> str:
    return fonte.replace("_", " ").title()


def formatar_pontos(pontos: list[str]) -> str:
    selecionados = pontos[:MAXIMO_DE_PONTOS_EXIBIDOS]
    return " · ".join(escape(ponto) for ponto in selecionados)


def formatar_requisitos(requisitos: list[str]) -> str:
    return " · ".join(escape(requisito) for requisito in requisitos)


def dividir_em_mensagens(texto: str) -> list[str]:
    if len(texto) <= LIMITE_DE_CARACTERES_DO_TELEGRAM:
        return [texto]
    mensagens: list[str] = []
    atual = ""
    for bloco in texto.split(SEPARADOR_ENTRE_VAGAS):
        candidato = bloco if not atual else atual + SEPARADOR_ENTRE_VAGAS + bloco
        if len(candidato) > LIMITE_DE_CARACTERES_DO_TELEGRAM and atual:
            mensagens.append(atual)
            atual = bloco
        else:
            atual = candidato
    mensagens.append(atual)
    return mensagens
