from datetime import date
from html import escape

from radar.domain.models import ResultadoMatch, Vaga

LIMITE_DE_CARACTERES_DO_TELEGRAM = 4096
MAXIMO_DE_PONTOS_EXIBIDOS = 3
SEPARADOR_ENTRE_VAGAS = "\n\n───────────────\n\n"
ROTULOS_MODALIDADE = {
    "remoto": "Remoto",
    "presencial": "Presencial",
    "hibrido": "Híbrido",
    "indiferente": "Indiferente",
}


def formatar_mensagem(resultados: list[ResultadoMatch], data: date) -> str:
    cabecalho = f"📡 <b>Radar de Estágio</b> — {data.strftime('%d/%m/%Y')}"
    if not resultados:
        return f"{cabecalho}\n\nNenhuma vaga compatível com o seu perfil hoje."
    ranqueados = sorted(resultados, key=lambda resultado: resultado.nota, reverse=True)
    blocos = [
        formatar_vaga(posicao, resultado) for posicao, resultado in enumerate(ranqueados, start=1)
    ]
    return cabecalho + "\n\n" + SEPARADOR_ENTRE_VAGAS.join(blocos)


def formatar_vaga(posicao: int, resultado: ResultadoMatch) -> str:
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
    linhas.append(f'🔗 <a href="{escape(vaga.url)}">Ver vaga</a>')
    return "\n".join(linhas)


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
