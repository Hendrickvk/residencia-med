"""
O "dia" da plataforma é o de Brasília (db.agora_br, decisão de 25/09). O servidor
e o banco rodam em UTC, e antes o dia virava às 21h daqui: quem estudava às 22h
caía no dia seguinte, e a ofensiva quebrava. Estes testes fixam o relógio às
22h30 de Brasília — 01h30 do dia seguinte em UTC — e conferem que tudo cai no dia
de Brasília.
"""

import datetime

import pytest

import db

NOITE = datetime.datetime(2026, 9, 25, 22, 30)  # 01h30 de 26/09 em UTC


@pytest.fixture()
def noite_em_brasilia(monkeypatch):
    monkeypatch.setattr(db, "agora_br", lambda: NOITE)
    return NOITE


def test_resposta_das_22h30_conta_no_dia_de_brasilia(usuario_teste, questao_teste, noite_em_brasilia):
    db.registrar_resposta(questao_teste, "A", True, usuario_id=usuario_teste)
    assert db.hoje_br() == datetime.date(2026, 9, 25)
    assert db.contar_respondidas_hoje(usuario_id=usuario_teste) == 1
    assert db.calcular_ofensiva(usuario_id=usuario_teste) == (1, True)


def test_teto_diario_conta_no_dia_de_brasilia(usuario_teste, noite_em_brasilia):
    db.consumir_cota_pratica(usuario_id=usuario_teste, quantidade=3)
    with db.get_conn() as conn:
        dia = conn.execute("SELECT dia FROM cota_pratica WHERE usuario_id = ?", (usuario_teste,)).fetchone()["dia"]
    assert dia == datetime.date(2026, 9, 25)


def test_relogio_da_plataforma_nao_e_o_do_servidor():
    # Brasília fica 3h atrás de UTC (2h, se o horário de verão voltar). O que
    # este teste pega é o relógio voltar a ser o do servidor, que é UTC.
    utc = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    atraso = utc - db.agora_br()
    assert datetime.timedelta(hours=2) <= atraso <= datetime.timedelta(hours=3, seconds=5)
