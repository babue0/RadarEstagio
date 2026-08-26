from radar.domain.models import Perfil, Vaga

INSTRUCAO_DO_RECRUTADOR = """\
Você é um recrutador experiente avaliando se uma vaga de estágio combina com um candidato.
Compare os requisitos da vaga com o perfil do candidato e responda em JSON com:
- nota: inteiro de 0 a 100 indicando a compatibilidade (100 = encaixe perfeito).
- motivo: uma única frase, em português, explicando a nota. Cite quantos requisitos o \
candidato cumpre e o que falta.
- alerta_pegadinha: uma frase curta se a vaga tiver sinal de problema (exige experiência \
de profissional pleno, não é da área do candidato, remuneração ausente, exclusividade de \
outro curso). Caso contrário, null.

Critérios de nota:
- Área e curso compatíveis pesam mais que habilidades específicas.
- Habilidades desejáveis ausentes reduzem pouco; obrigatórias ausentes reduzem muito.
- Modalidade incompatível com a preferência do candidato reduz a nota.
- Vaga fora da área de tecnologia deve receber nota abaixo de 30.
"""


def descrever_perfil(perfil: Perfil) -> str:
    return (
        f"Curso: {perfil.curso}\n"
        f"Período: {perfil.periodo}º\n"
        f"Habilidades: {', '.join(perfil.habilidades)}\n"
        f"Cidade: {perfil.cidade}\n"
        f"Modalidade preferida: {perfil.modalidade.value}"
    )


def descrever_vaga(vaga: Vaga) -> str:
    return (
        f"Título: {vaga.titulo}\n"
        f"Empresa: {vaga.empresa}\n"
        f"Localização: {vaga.localizacao}\n"
        f"Descrição: {vaga.descricao}"
    )


def montar_prompt(vaga: Vaga, perfil: Perfil) -> str:
    return (
        f"{INSTRUCAO_DO_RECRUTADOR}\n"
        f"## Candidato\n{descrever_perfil(perfil)}\n\n"
        f"## Vaga\n{descrever_vaga(vaga)}\n"
    )
