from radar.domain.models import Perfil, Vaga

INSTRUCAO_DO_RECRUTADOR = """\
Você é um recrutador experiente avaliando se vagas de estágio combinam com um candidato.
Compare os requisitos de cada vaga com o perfil do candidato e responda em JSON com a lista \
"avaliacoes", contendo exatamente um item por vaga recebida, com:
- id_vaga: o id informado no título da vaga, copiado sem alteração.
- nota: inteiro de 0 a 100 indicando a compatibilidade (100 = encaixe perfeito).
- pontos_a_favor: lista com até 3 itens do que a vaga tem em comum com o candidato. \
Cada item com no máximo 4 palavras, citando o nome concreto (ex.: "Python", "SQL", \
"Remoto", "Área de desenvolvimento"). Lista vazia se não houver nada em comum.
- pontos_contra: lista com até 3 itens do que a vaga pede e o candidato não tem, ou do que \
não bate com a preferência dele. Cada item com no máximo 4 palavras e concreto (ex.: \
"Exige Java avançado", "Presencial em São Paulo", "Foco em suporte"). Nunca escreva \
"1 requisito" ou "alguns requisitos": diga qual.
- alerta_pegadinha: no máximo 10 palavras, apenas se a vaga esconder um problema que o \
título não revela: exige experiência de pleno/sênior, é comercial ou operacional \
disfarçada de TI, sem remuneração, exclusiva de outro curso. Nunca repita o que já está \
nos pontos contra. Localização e modalidade não são pegadinha: vão nos pontos contra. Se não \
houver pegadinha, null.

Critérios de nota:
- Área e curso compatíveis pesam mais que habilidades específicas.
- Habilidades desejáveis ausentes reduzem pouco; obrigatórias ausentes reduzem muito.
- Modalidade: use somente o que a descrição diz. Nunca deduza que a vaga é presencial \
pela cidade. Se a descrição não informa a modalidade, inclua "Modalidade não informada" \
nos pontos contra e reduza a nota em cerca de 10 pontos. Se a vaga é remota, a cidade não \
importa e não deve ser ponto contra. Se a vaga é explicitamente presencial ou híbrida e o \
candidato prefere remoto, nota máxima 30.
- Vaga fora da área de tecnologia deve receber nota abaixo de 30.
- Avalie cada vaga por seus próprios requisitos; não misture informações entre vagas.
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
        f"### Vaga id={vaga.id_externo}\n"
        f"Título: {vaga.titulo}\n"
        f"Empresa: {vaga.empresa}\n"
        f"Localização: {vaga.localizacao}\n"
        f"Descrição: {vaga.descricao}"
    )


def montar_prompt(vagas: list[Vaga], perfil: Perfil) -> str:
    descricoes = "\n\n".join(descrever_vaga(vaga) for vaga in vagas)
    return (
        f"{INSTRUCAO_DO_RECRUTADOR}\n"
        f"## Candidato\n{descrever_perfil(perfil)}\n\n"
        f"## Vagas ({len(vagas)})\n{descricoes}\n"
    )
