from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from radar.domain.models import Modalidade, Perfil, ResultadoMatch, Usuario, Vaga
from radar.domain.perfil_fixo import perfil_do_mvp


def vaga_exemplo() -> Vaga:
    return Vaga(
        id_externo="123",
        fonte="adzuna",
        titulo="Estágio em Desenvolvimento",
        empresa="Empresa Exemplo",
        localizacao="Rio de Janeiro, RJ",
        descricao="Vaga de estágio para desenvolvimento web.",
        url="https://exemplo.com/vaga/123",
        publicada_em=datetime(2026, 8, 25, 8, 0),
    )


def test_vaga_nasce_sem_modalidade_informada():
    assert vaga_exemplo().modalidade is None


def test_vaga_aceita_modalidade_informada_pela_fonte():
    vaga = vaga_exemplo().model_copy(update={"modalidade": Modalidade.REMOTO})
    assert vaga.modalidade is Modalidade.REMOTO


def test_resultado_match_aceita_nota_nos_limites():
    for nota in (0, 100):
        resultado = ResultadoMatch(vaga=vaga_exemplo(), nota=nota)
        assert resultado.nota == nota


@pytest.mark.parametrize("nota", [-1, 101])
def test_resultado_match_rejeita_nota_fora_do_intervalo(nota):
    with pytest.raises(ValidationError):
        ResultadoMatch(vaga=vaga_exemplo(), nota=nota)


def test_resultado_match_alerta_pegadinha_e_opcional():
    resultado = ResultadoMatch(vaga=vaga_exemplo(), nota=80)
    assert resultado.alerta_pegadinha is None


def test_perfil_rejeita_modalidade_invalida():
    with pytest.raises(ValidationError):
        Perfil(
            curso="Engenharia de Software",
            periodo=4,
            habilidades=["Python"],
            cidade="Rio de Janeiro, RJ",
            modalidade="qualquer",
        )


def test_perfil_rejeita_lista_de_habilidades_vazia():
    with pytest.raises(ValidationError):
        Perfil(
            curso="Engenharia de Software",
            periodo=4,
            habilidades=[],
            cidade="Rio de Janeiro, RJ",
            modalidade=Modalidade.REMOTO,
        )


def test_perfil_do_mvp_e_valido():
    perfil = perfil_do_mvp()
    assert perfil.modalidade is Modalidade.PRESENCIAL
    assert perfil.habilidades == ["Python", "Java"]


def test_usuario_exige_chat_id_preenchido():
    with pytest.raises(ValidationError):
        Usuario(id=uuid4(), perfil=perfil_do_mvp(), chat_id="")
