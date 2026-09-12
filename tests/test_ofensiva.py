import datetime

import db


def test_ofensiva_zero_sem_respostas(usuario_teste):
    dias, respondeu_hoje = db.calcular_ofensiva(usuario_id=usuario_teste)
    assert dias == 0
    assert respondeu_hoje is False


def test_ofensiva_um_dia_apos_responder_hoje(usuario_teste, questao_teste):
    db.registrar_resposta(questao_teste, "A", True, usuario_id=usuario_teste)
    dias, respondeu_hoje = db.calcular_ofensiva(usuario_id=usuario_teste)
    assert dias == 1
    assert respondeu_hoje is True


def test_ofensiva_de_ontem_ainda_conta_se_hoje_nao_respondeu(usuario_teste, questao_teste):
    ontem = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    db.registrar_resposta(questao_teste, "A", True, usuario_id=usuario_teste)
    with db.get_conn() as conn:
        conn.execute("UPDATE respostas SET respondida_em = ? WHERE usuario_id = ?", (ontem, usuario_teste))
    dias, respondeu_hoje = db.calcular_ofensiva(usuario_id=usuario_teste)
    assert respondeu_hoje is False
    assert dias == 1


def test_ofensiva_quebra_com_um_dia_de_buraco(usuario_teste, questao_teste):
    anteontem = (datetime.date.today() - datetime.timedelta(days=2)).isoformat()
    db.registrar_resposta(questao_teste, "A", True, usuario_id=usuario_teste)
    with db.get_conn() as conn:
        conn.execute("UPDATE respostas SET respondida_em = ? WHERE usuario_id = ?", (anteontem, usuario_teste))
    dias, respondeu_hoje = db.calcular_ofensiva(usuario_id=usuario_teste)
    assert dias == 0
    assert respondeu_hoje is False
