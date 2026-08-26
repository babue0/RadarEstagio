from radar.domain.models import Modalidade, Perfil


def perfil_do_mvp() -> Perfil:
    return Perfil(
        curso="Engenharia de Software",
        periodo=4,
        habilidades=["Python", "Git", "JavaScript", "React", "SQL", "Java"],
        cidade="Rio de Janeiro, RJ",
        modalidade=Modalidade.REMOTO,
    )
