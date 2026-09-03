from datetime import UTC, datetime

import pytest

from radar.domain.models import ExtracaoDaVaga, NivelCompatibilidade, Vaga
from radar.matching.errors import CotaDeAvaliacaoExcedida, ErroDeAvaliacao
from radar.matching.lotes import ExtratorEmLotes


def vaga(numero: int) -> Vaga:
    return Vaga(
        id_externo=str(numero),
        fonte="adzuna",
        titulo=f"Estágio {numero}",
        empresa="Empresa",
        localizacao="Rio de Janeiro",
        descricao="descrição",
        url=f"https://exemplo.com/vaga/{numero}",
        publicada_em=datetime(2026, 8, 25, tzinfo=UTC),
    )


def vagas(quantidade: int) -> list[Vaga]:
    return [vaga(numero) for numero in range(1, quantidade + 1)]


class ExtratorDeLoteFalso:
    def __init__(
        self,
        falhas_por_lote: dict[tuple[str, ...], Exception] | None = None,
        ids_omitidos: set[str] | None = None,
        ids_omitidos_apenas_em_lote: set[str] | None = None,
        erros_por_vaga: dict[str, Exception] | None = None,
        falhas_temporarias_por_lote: dict[tuple[str, ...], Exception] | None = None,
    ) -> None:
        self._falhas_por_lote = falhas_por_lote or {}
        self._falhas_temporarias_por_lote = dict(falhas_temporarias_por_lote or {})
        self._ids_omitidos = ids_omitidos or set()
        self._ids_omitidos_apenas_em_lote = ids_omitidos_apenas_em_lote or set()
        self._erros_por_vaga = erros_por_vaga or {}
        self.lotes_recebidos: list[list[str]] = []

    def extrair(self, lote: list[Vaga]) -> list[ExtracaoDaVaga]:
        ids = tuple(vaga.id_externo for vaga in lote)
        self.lotes_recebidos.append(list(ids))
        if ids in self._falhas_por_lote:
            raise self._falhas_por_lote[ids]
        if ids in self._falhas_temporarias_por_lote:
            raise self._falhas_temporarias_por_lote.pop(ids)
        for vaga in lote:
            if vaga.id_externo in self._erros_por_vaga:
                raise self._erros_por_vaga[vaga.id_externo]
        omitidos = set(self._ids_omitidos)
        if len(lote) > 1:
            omitidos |= self._ids_omitidos_apenas_em_lote
        return [
            ExtracaoDaVaga(
                id_vaga=vaga.id_externo,
                area_de_tecnologia=NivelCompatibilidade.COMPATIVEL,
            )
            for vaga in lote
            if vaga.id_externo not in omitidos
        ]


def ids_de(extracoes: list[ExtracaoDaVaga]) -> list[str]:
    return [extracao.id_vaga for extracao in extracoes]


def test_divide_as_vagas_em_lotes_do_tamanho_configurado():
    interno = ExtratorDeLoteFalso()

    resultados = ExtratorEmLotes(interno, 4).extrair(vagas(10))

    assert interno.lotes_recebidos == [["1", "2", "3", "4"], ["5", "6", "7", "8"], ["9", "10"]]
    assert ids_de(resultados) == [str(numero) for numero in range(1, 11)]


def test_lista_vazia_nao_chama_o_avaliador_interno():
    interno = ExtratorDeLoteFalso()

    assert ExtratorEmLotes(interno, 4).extrair([]) == []
    assert interno.lotes_recebidos == []


def test_lote_que_falha_e_dividido_ao_meio_ate_isolar_a_vaga_com_problema():
    interno = ExtratorDeLoteFalso(erros_por_vaga={"3": ErroDeAvaliacao("JSON inválido")})

    resultados = ExtratorEmLotes(interno, 4).extrair(vagas(4))

    assert interno.lotes_recebidos == [["1", "2", "3", "4"], ["1", "2"], ["3", "4"], ["3"], ["4"]]
    assert ids_de(resultados) == ["1", "2", "4"]


def test_vaga_omitida_pelo_modelo_e_reavaliada_sozinha():
    interno = ExtratorDeLoteFalso(ids_omitidos_apenas_em_lote={"2"})

    resultados = ExtratorEmLotes(interno, 3).extrair(vagas(3))

    assert interno.lotes_recebidos == [["1", "2", "3"], ["2"]]
    assert sorted(ids_de(resultados)) == ["1", "2", "3"]


def test_vaga_omitida_mesmo_sozinha_e_ignorada():
    interno = ExtratorDeLoteFalso(ids_omitidos={"2"})

    resultados = ExtratorEmLotes(interno, 3).extrair(vagas(3))

    assert interno.lotes_recebidos == [["1", "2", "3"], ["2"]]
    assert ids_de(resultados) == ["1", "3"]


def test_cota_excedida_aguarda_o_tempo_pedido_e_tenta_o_mesmo_lote_de_novo():
    interno = ExtratorDeLoteFalso(
        falhas_temporarias_por_lote={("3", "4"): CotaDeAvaliacaoExcedida("HTTP 429", 15.3)}
    )
    esperas: list[float] = []

    resultados = ExtratorEmLotes(interno, 2, esperar=esperas.append).extrair(vagas(6))

    assert esperas == [16.3]
    assert interno.lotes_recebidos == [["1", "2"], ["3", "4"], ["3", "4"], ["5", "6"]]
    assert ids_de(resultados) == ["1", "2", "3", "4", "5", "6"]


def test_cota_excedida_sem_tempo_indicado_espera_um_minuto():
    interno = ExtratorDeLoteFalso(
        falhas_temporarias_por_lote={("1", "2"): CotaDeAvaliacaoExcedida("HTTP 429")}
    )
    esperas: list[float] = []

    ExtratorEmLotes(interno, 2, esperar=esperas.append).extrair(vagas(2))

    assert esperas == [61]


def test_cota_excedida_persistente_desiste_apos_as_tentativas_e_devolve_o_que_ja_tem():
    interno = ExtratorDeLoteFalso(
        falhas_por_lote={("3", "4"): CotaDeAvaliacaoExcedida("HTTP 429", 15)}
    )
    esperas: list[float] = []

    resultados = ExtratorEmLotes(interno, 2, esperar=esperas.append).extrair(vagas(6))

    assert esperas == [16, 16, 16]
    assert interno.lotes_recebidos == [["1", "2"], ["3", "4"], ["3", "4"], ["3", "4"], ["3", "4"]]
    assert ids_de(resultados) == ["1", "2"]


def test_cota_excedida_com_espera_longa_interrompe_sem_aguardar():
    interno = ExtratorDeLoteFalso(
        falhas_por_lote={("3", "4"): CotaDeAvaliacaoExcedida("HTTP 429", 3600)}
    )
    esperas: list[float] = []

    resultados = ExtratorEmLotes(interno, 2, esperar=esperas.append).extrair(vagas(6))

    assert esperas == []
    assert interno.lotes_recebidos == [["1", "2"], ["3", "4"]]
    assert ids_de(resultados) == ["1", "2"]


def test_cota_excedida_nao_e_dividida_ao_meio():
    interno = ExtratorDeLoteFalso(
        falhas_por_lote={("1", "2", "3", "4"): CotaDeAvaliacaoExcedida("HTTP 429", 3600)}
    )

    resultados = ExtratorEmLotes(interno, 4, esperar=lambda _: None).extrair(vagas(4))

    assert interno.lotes_recebidos == [["1", "2", "3", "4"]]
    assert resultados == []


def test_tamanho_de_lote_invalido_e_rejeitado():
    with pytest.raises(ValueError):
        ExtratorEmLotes(ExtratorDeLoteFalso(), 0)


def test_conta_uma_requisicao_por_lote_enviado_ao_avaliador():
    avaliador = ExtratorDeLoteFalso()
    em_lotes = ExtratorEmLotes(avaliador, tamanho_do_lote=10)

    em_lotes.extrair(vagas(25))

    assert em_lotes.requisicoes == 3
    assert len(avaliador.lotes_recebidos) == 3
