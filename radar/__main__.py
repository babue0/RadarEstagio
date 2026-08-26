from pydantic import ValidationError

from radar.settings import Settings


def nomes_das_variaveis_ausentes(erro: ValidationError) -> list[str]:
    return [
        str(detalhe["loc"][0]).upper() for detalhe in erro.errors() if detalhe["type"] == "missing"
    ]


def main() -> None:
    try:
        settings = Settings()
    except ValidationError as erro:
        print("Variáveis de ambiente ausentes:")
        for nome in nomes_das_variaveis_ausentes(erro):
            print(f"  - {nome}")
        return

    print("Configuração carregada com sucesso.")
    print(f"Dias recentes na Adzuna: {settings.adzuna_dias_recentes}")
    print(f"Vagas enviadas por execução: {settings.quantidade_vagas_enviadas}")


if __name__ == "__main__":
    main()
