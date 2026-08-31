from radar.domain.models import AreaDeInteresse, Modalidade, Perfil


def perfil_do_mvp() -> Perfil:
    return Perfil(
        curso="Engenharia de Software",
        periodo=4,
        habilidades=["Python", "Git", "Java", "SQL"],
        cidade="Rio de Janeiro, RJ",
        modalidade=Modalidade.PRESENCIAL,
        areas_de_interesse=[AreaDeInteresse.DESENVOLVIMENTO_WEB],
    )
