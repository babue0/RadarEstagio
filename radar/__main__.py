from pydantic import ValidationError

from radar.settings import Settings

TIPOS_DE_ERRO_DE_PREENCHIMENTO = frozenset({"missing", "string_too_short"})


def nomes_das_variaveis_nao_preenchidas(erro: ValidationError) -> list[str]:
    return [
        str(detalhe["loc"][0]).upper()
        for detalhe in erro.errors()
        if detalhe["type"] in TIPOS_DE_ERRO_DE_PREENCHIMENTO
    ]


def main() -> None:
    try:
        settings = Settings()
    except ValidationError as erro:
        print("Variáveis de ambiente ausentes ou vazias:")
        for nome in nomes_das_variaveis_nao_preenchidas(erro):
            print(f"  - {nome}")
        return

    print("Configuração carregada com sucesso.")
    print(f"Dias recentes na Adzuna: {settings.adzuna_dias_recentes}")
    print(f"Vagas enviadas por execução: {settings.quantidade_vagas_enviadas}")


if __name__ == "__main__":
    main()
