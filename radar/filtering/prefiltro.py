import re
import unicodedata

from radar.domain.models import Modalidade, Perfil, Vaga

PADRAO_ESTAGIO = re.compile(r"\bestagi|\bintern(?:ship)?s?\b")
PADRAO_SENIORIDADE = re.compile(r"\b(?:pleno|senior|especialista|coordenador)\b")
PADRAO_ANOS_DE_EXPERIENCIA = re.compile(
    r"(\d+)\s*\+?\s*anos?\s+(?:de\s+)?experiencia"
    r"|experiencia\s+(?:minima\s+)?(?:de\s+)?(\d+)\s*\+?\s*anos?"
)
PADRAO_OUTRA_AREA = re.compile(
    r"\b(?:eletronic[ao]|eletrotecnic[ao]|mecanic[ao]|civil|quimic[ao]|ambiental"
    r"|fisioterapia|enfermagem|nutricao|psicologia|pedagogia|juridic[ao]|direito"
    r"|financeir[ao]|contabil|contabilidade|recursos humanos|rh|manufatura|producao"
    r"|marketing|endomarketing|comercial|vendas|pre-?vendas?|logistica"
    r"|arquitetura e urbanismo|design de interiores|comercio exterior|farmacia|turismo"
    r"|hotelaria|gastronomia|embalagens|treinamento e desenvolvimento"
    r"|recrutamento e selecao|r&s|people|compliance"
    r"|atuari\w*|auditoria|comunicacao|imprensa|crm|laboratorio|inteligencia de mercado"
    r"|backoffice|processos administrativos)\b"
)
PADRAO_AREA_NO_TITULO = re.compile(
    r"\b(?:ti|t\.i\.?|tech|tecnologia|software|desenvolvimento|desenvolvedor[a]?|dev"
    r"|developer|programacao|programador[a]?|dados|data|sistemas?|computacao|informatica"
    r"|infra(?:estrutura)?|redes|seguranca da informacao|cyber\w*|cloud|devops"
    r"|machine learning|inteligencia artificial|ia|front-?end|back-?end|full-?stack"
    r"|qa|testes?|suporte|help-? ?desk|banco de dados|sql|python|java(?:script)?|web"
    r"|mobile|analytics|bi|business intelligence|produto|ux|ui|automacao|rpa|digital"
    r"|inovacao|engenharia de software|ciencia da computacao|sistemas de informacao"
    r"|ciencia de dados|analise de sistemas)\b"
)
PADRAO_AREA_NA_DESCRICAO = re.compile(
    r"\b(?:tecnologia da informacao|ciencia da computacao|engenharia de software"
    r"|engenharia da computacao|sistemas de informacao|analise e desenvolvimento de sistemas"
    r"|ciencia de dados|analise de dados|engenharia de dados|banco de dados"
    r"|desenvolvimento de (?:software|sistemas|aplicacoes|aplicativos|web)|programacao"
    r"|programador[a]?|desenvolvedor[a]?|linguagem de programacao|python|java(?:script)?"
    r"|sql|suporte tecnico|help-? ?desk|infraestrutura de ti|redes de computadores"
    r"|seguranca da informacao|machine learning|inteligencia artificial|power bi|devops"
    r"|cloud|front-?end|back-?end|full-?stack)\b"
)
PADRAO_TRABALHO_REMOTO = re.compile(r"\b(?:remoto|remota|remote|home\s*office)\b")
PADRAO_TRABALHO_PRESENCIAL = re.compile(r"\b(?:presencial(?:mente)?|hibrid[oa]|hybrid|on-?site)\b")
ANOS_DE_EXPERIENCIA_QUE_DESCARTAM = range(2, 10)


def normalizar(texto: str) -> str:
    sem_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return sem_acentos.casefold()


def nao_e_estagio(vaga: Vaga) -> bool:
    return PADRAO_ESTAGIO.search(normalizar(vaga.titulo)) is None


def exige_senioridade(vaga: Vaga) -> bool:
    return PADRAO_SENIORIDADE.search(normalizar(vaga.titulo)) is not None


def fora_da_area_de_tecnologia(vaga: Vaga) -> bool:
    titulo = normalizar(vaga.titulo)
    if PADRAO_OUTRA_AREA.search(titulo):
        return True
    if PADRAO_AREA_NO_TITULO.search(titulo):
        return False
    return PADRAO_AREA_NA_DESCRICAO.search(normalizar(vaga.descricao)) is None


def exige_anos_de_experiencia(vaga: Vaga) -> bool:
    texto = normalizar(f"{vaga.titulo} {vaga.descricao}")
    anos_mencionados = (
        int(grupo)
        for ocorrencia in PADRAO_ANOS_DE_EXPERIENCIA.finditer(texto)
        for grupo in ocorrencia.groups()
        if grupo
    )
    return any(anos in ANOS_DE_EXPERIENCIA_QUE_DESCARTAM for anos in anos_mencionados)


def localizacao_incompativel(vaga: Vaga, perfil: Perfil) -> bool:
    if perfil.modalidade is not Modalidade.PRESENCIAL:
        return False
    return cidade(perfil.cidade) != cidade(vaga.localizacao)


def cidade(localizacao: str) -> str:
    return normalizar(localizacao.split(",")[0]).strip()


def modalidade_incompativel(vaga: Vaga, perfil: Perfil) -> bool:
    if perfil.modalidade is not Modalidade.REMOTO:
        return False
    if vaga.modalidade is not None:
        return vaga.modalidade is not Modalidade.REMOTO
    texto = normalizar(f"{vaga.titulo} {vaga.descricao}")
    exige_presenca = PADRAO_TRABALHO_PRESENCIAL.search(texto) is not None
    admite_remoto = PADRAO_TRABALHO_REMOTO.search(texto) is not None
    return exige_presenca and not admite_remoto


def deve_descartar(vaga: Vaga, perfil: Perfil) -> bool:
    return (
        nao_e_estagio(vaga)
        or exige_senioridade(vaga)
        or fora_da_area_de_tecnologia(vaga)
        or exige_anos_de_experiencia(vaga)
        or localizacao_incompativel(vaga, perfil)
        or modalidade_incompativel(vaga, perfil)
    )


def filtrar(vagas: list[Vaga], perfil: Perfil) -> list[Vaga]:
    return [vaga for vaga in vagas if not deve_descartar(vaga, perfil)]
