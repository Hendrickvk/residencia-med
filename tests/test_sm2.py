"""
Cobertura do SM-2 (`repeticao_espacada.py`) — a "única rede de segurança da
migração" segundo MIGRACAO.md §4. Fonte de verdade continua sendo Python;
estes testes existem para que ninguém precise reimplementar isso em TS
"para conferir se está certo".
"""

import datetime

import db
import repeticao_espacada as sr


def test_primeira_revisao_boa_agenda_para_amanha(usuario_teste, questao_teste):
    antes = datetime.datetime.now()
    sr.registrar_revisao(questao_teste, 5, usuario_id=usuario_teste)
    depois = datetime.datetime.now()
    estado = sr.obter_estado(questao_teste, usuario_id=usuario_teste)
    assert estado["repeticoes"] == 1
    assert estado["intervalo_dias"] == 1
    assert antes + datetime.timedelta(days=1) <= estado["proxima_revisao"] <= depois + datetime.timedelta(days=1)


def test_segunda_revisao_boa_pula_para_seis_dias(usuario_teste, questao_teste):
    sr.registrar_revisao(questao_teste, 5, usuario_id=usuario_teste)
    sr.registrar_revisao(questao_teste, 5, usuario_id=usuario_teste)
    estado = sr.obter_estado(questao_teste, usuario_id=usuario_teste)
    assert estado["repeticoes"] == 2
    assert estado["intervalo_dias"] == 6


def test_terceira_revisao_boa_multiplica_intervalo_pela_facilidade(usuario_teste, questao_teste):
    sr.registrar_revisao(questao_teste, 5, usuario_id=usuario_teste)
    sr.registrar_revisao(questao_teste, 5, usuario_id=usuario_teste)
    estado_antes = sr.obter_estado(questao_teste, usuario_id=usuario_teste)
    sr.registrar_revisao(questao_teste, 5, usuario_id=usuario_teste)
    estado = sr.obter_estado(questao_teste, usuario_id=usuario_teste)
    assert estado["repeticoes"] == 3
    assert estado["intervalo_dias"] == round(6 * estado_antes["facilidade"])


def test_erro_reinicia_o_ciclo_mesmo_apos_progresso(usuario_teste, questao_teste):
    sr.registrar_revisao(questao_teste, 5, usuario_id=usuario_teste)
    sr.registrar_revisao(questao_teste, 5, usuario_id=usuario_teste)
    sr.registrar_revisao(questao_teste, 1, usuario_id=usuario_teste)
    estado = sr.obter_estado(questao_teste, usuario_id=usuario_teste)
    assert estado["repeticoes"] == 0
    assert estado["intervalo_dias"] == 1


def test_facilidade_nunca_cai_abaixo_do_piso(usuario_teste, questao_teste):
    for _ in range(10):
        sr.registrar_revisao(questao_teste, 0, usuario_id=usuario_teste)
    estado = sr.obter_estado(questao_teste, usuario_id=usuario_teste)
    assert estado["facilidade"] >= 1.3


def test_avaliar_revisao_desmarca_quando_nao_e_erro(usuario_teste, questao_teste):
    db.marcar_questao(usuario_teste, questao_teste)
    assert db.questao_esta_marcada(usuario_teste, questao_teste)
    sr.avaliar_revisao(questao_teste, 4, usuario_id=usuario_teste)
    assert not db.questao_esta_marcada(usuario_teste, questao_teste)


def test_avaliar_revisao_mantem_marcada_quando_e_erro(usuario_teste, questao_teste):
    db.marcar_questao(usuario_teste, questao_teste)
    sr.avaliar_revisao(questao_teste, 1, usuario_id=usuario_teste)
    assert db.questao_esta_marcada(usuario_teste, questao_teste)


def test_fila_revisao_inclui_questao_nunca_revisada(usuario_teste, questao_teste):
    fila = sr.fila_revisao(usuario_id=usuario_teste)
    assert any(q["id"] == questao_teste for q in fila)


def test_fila_revisao_nao_duplica_questao_pendente_e_marcada(usuario_teste, questao_teste):
    sr.registrar_revisao(questao_teste, 1, usuario_id=usuario_teste)
    with db.get_conn() as conn:
        conn.execute(
            "UPDATE revisao SET proxima_revisao = ? WHERE usuario_id = ? AND questao_id = ?",
            (datetime.datetime.now(), usuario_teste, questao_teste),
        )
    db.marcar_questao(usuario_teste, questao_teste)
    fila = sr.fila_revisao(usuario_id=usuario_teste)
    ids = [q["id"] for q in fila]
    assert ids.count(questao_teste) == 1


def test_erro_agenda_de_verdade_em_10_minutos_nao_no_dia_seguinte(usuario_teste, questao_teste):
    """Regressão da dívida do HANDOFF_REDESIGN.md: antes da migração pra
    TIMESTAMP, 'Errei — 10 min' persistia como amanhã no banco (só
    'voltava logo' via hack no session_state do Streamlit)."""
    antes = datetime.datetime.now()
    sr.registrar_revisao(questao_teste, 1, usuario_id=usuario_teste)
    estado = sr.obter_estado(questao_teste, usuario_id=usuario_teste)
    delta = estado["proxima_revisao"] - antes
    assert datetime.timedelta(minutes=9) < delta < datetime.timedelta(minutes=11)
    assert estado["proxima_revisao"] < antes + datetime.timedelta(hours=1)


def test_questao_com_erro_nao_aparece_como_pendente_antes_de_10_minutos(usuario_teste, questao_teste):
    sr.registrar_revisao(questao_teste, 1, usuario_id=usuario_teste)
    pendentes = sr.questoes_para_revisar_hoje(usuario_id=usuario_teste)
    assert questao_teste not in [q["id"] for q in pendentes]
