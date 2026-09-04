from radar.domain.models import FunilDaCoorte

LARGURA_DO_ROTULO = 26


def formatar_funil(funil: FunilDaCoorte) -> str:
    linhas = [
        f"Funil da coorte — perfis criados nos últimos {funil.dias} dias",
        "",
        etapa("Perfis criados", funil.perfis_criados, funil.perfis_criados),
        etapa("Telegram vinculado", funil.perfis_vinculados, funil.perfis_criados),
        etapa("Primeira recomendação", funil.perfis_ativados, funil.perfis_criados),
        etapa("Abriram uma vaga", funil.perfis_com_vaga_aberta, funil.perfis_criados),
        etapa("Marcaram como útil", funil.perfis_com_vaga_util, funil.perfis_criados),
        etapa("Iniciaram candidatura", funil.perfis_com_candidatura, funil.perfis_criados),
        "",
        etapa("Vagas enviadas", funil.vagas_enviadas, funil.vagas_enviadas),
        etapa("Aberturas", funil.vagas_abertas, funil.vagas_enviadas),
        etapa("Marcadas como úteis", funil.vagas_uteis, funil.vagas_enviadas),
        etapa("Marcadas como irrelevantes", funil.vagas_irrelevantes, funil.vagas_enviadas),
        etapa("Candidaturas", funil.candidaturas, funil.vagas_enviadas),
        "",
        "Motivo da recusa:",
    ]
    linhas.extend(linhas_dos_motivos(funil))
    linhas.extend(["", linha_do_custo(funil)])
    return "\n".join(linhas)


def etapa(rotulo: str, valor: int, total: int) -> str:
    return f"{rotulo:<{LARGURA_DO_ROTULO}}{valor:>5}{proporcao(valor, total)}"


def proporcao(valor: int, total: int) -> str:
    if not total or valor == total:
        return ""
    return f"  ({round(100 * valor / total)}%)"


def linhas_dos_motivos(funil: FunilDaCoorte) -> list[str]:
    if not funil.recusas_por_motivo:
        return ["  nenhuma recusa registrada"]
    return [
        f"  {motivo:<{LARGURA_DO_ROTULO}}{total:>3}"
        for motivo, total in funil.recusas_por_motivo.items()
    ]


def linha_do_custo(funil: FunilDaCoorte) -> str:
    extraidas = funil.vagas_extraidas
    por_ativado = funil.vagas_extraidas_por_ativado()
    if por_ativado is None:
        return f"Custo: {extraidas} vagas extraídas, nenhum usuário ativado no período"
    return f"Custo: {extraidas} vagas extraídas, {por_ativado:.1f} por usuário ativado"
