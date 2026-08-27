from datetime import date
from html import escape

from radar.domain.models import ResultadoMatch

LIMITE_DE_CARACTERES_DO_TELEGRAM = 4096
SEPARADOR_ENTRE_VAGAS = "\n\n───────────────\n\n"


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
        f"Nota {resultado.nota}",
    ]
    if resultado.pontos_a_favor:
        linhas.append(f"✅ {formatar_pontos(resultado.pontos_a_favor)}")
    if resultado.pontos_contra:
        linhas.append(f"❌ {formatar_pontos(resultado.pontos_contra)}")
    if resultado.alerta_pegadinha:
        linhas.append(f"⚠️ {escape(resultado.alerta_pegadinha)}")
    linhas.append(f'🔗 <a href="{escape(vaga.url)}">Ver vaga</a>')
    return "\n".join(linhas)


def formatar_pontos(pontos: list[str]) -> str:
    return " · ".join(escape(ponto) for ponto in pontos)


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
