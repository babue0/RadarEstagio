from radar.domain.models import AreaDeInteresse, Modalidade, Perfil


def perfil_de_exemplo() -> Perfil:
    return Perfil(
        curso="Ciência da Computação",
        periodo=5,
        habilidades=[
            "Python",
            "JavaScript",
            "SQL",
            "HTML",
            "CSS",
            "Git",
            "Lógica de Programação",
        ],
        cidade="São Paulo, SP",
        modalidade=Modalidade.HIBRIDO,
        areas_de_interesse=[AreaDeInteresse.DESENVOLVIMENTO_WEB, AreaDeInteresse.DADOS_IA],
    )
