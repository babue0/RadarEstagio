from radar.domain.models import Modalidade, Perfil, ResultadoMatch

LIMITE_MODALIDADE_NAO_INFORMADA = 85
LIMITE_MODALIDADE_INCOMPATIVEL = 30
AVISO_MODALIDADE_NAO_INFORMADA = "Nota limitada a 85: modalidade não informada"
AVISO_MODALIDADE_INCOMPATIVEL = "Nota limitada a 30: modalidade incompatível"
TERMOS_DE_MODALIDADE = (
    "modalidade",
    "presencial",
    "híbrido",
    "hibrido",
    "híbrida",
    "hibrida",
    "remoto",
    "remota",
)


def aplicar_regras_objetivas(
    resultados: list[ResultadoMatch], perfil: Perfil
) -> list[ResultadoMatch]:
    return [aplicar_regras_ao_resultado(resultado, perfil) for resultado in resultados]


def aplicar_regras_ao_resultado(resultado: ResultadoMatch, perfil: Perfil) -> ResultadoMatch:
    limite, aviso = limite_de_modalidade(resultado, perfil)
    nota = min(resultado.nota, limite)
    avisos = list(resultado.avisos_objetivos)
    if nota < resultado.nota and aviso not in avisos:
        avisos.append(aviso)
    pontos_contra = [ponto for ponto in resultado.pontos_contra if not descreve_modalidade(ponto)]
    return resultado.model_copy(
        update={
            "nota": nota,
            "pontos_contra": pontos_contra,
            "avisos_objetivos": avisos,
        }
    )


def limite_de_modalidade(resultado: ResultadoMatch, perfil: Perfil) -> tuple[int, str]:
    modalidade = resultado.vaga.modalidade
    if modalidade is None:
        return LIMITE_MODALIDADE_NAO_INFORMADA, AVISO_MODALIDADE_NAO_INFORMADA
    if perfil.modalidade is Modalidade.REMOTO and modalidade in {
        Modalidade.PRESENCIAL,
        Modalidade.HIBRIDO,
    }:
        return LIMITE_MODALIDADE_INCOMPATIVEL, AVISO_MODALIDADE_INCOMPATIVEL
    return 100, ""


def descreve_modalidade(ponto: str) -> bool:
    normalizado = ponto.casefold()
    return any(termo in normalizado for termo in TERMOS_DE_MODALIDADE)
