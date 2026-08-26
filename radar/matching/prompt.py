from radar.domain.models import Perfil, Vaga

INSTRUCAO_DO_RECRUTADOR = """\
Você é um recrutador experiente avaliando se uma vaga de estágio combina com um candidato.
Compare os requisitos da vaga com o perfil do candidato e responda em JSON com:
- nota: inteiro de 0 a 100 indicando a compatibilidade (100 = encaixe perfeito).
- motivo: uma única frase em português com no máximo 15 palavras explicando a nota. \
Diga quantos requisitos o candidato cumpre e o principal que falta. Sem rodeios.
- alerta_pegadinha: no máximo 10 palavras, apenas se a vaga esconder um problema que o \
título não revela: exige experiência de pleno/sênior, é comercial ou operacional \
disfarçada de TI, sem remuneração, exclusiva de outro curso. Nunca repita o que já está \
no motivo. Localização e modalidade não são pegadinha: vão no motivo, não aqui. Se não \
houver pegadinha, null.

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
