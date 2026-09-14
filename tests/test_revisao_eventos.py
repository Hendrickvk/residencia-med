"""
Revisão que mede (fase 1): histórico de avaliações em `revisao_eventos`,
prazo previsto nos botões igual ao agendado, e o gabarito decidindo o erro
quando o aluno responde de novo na Revisão.
"""

import datetime

import db
import repeticao_espacada as sr


def _eventos(usuario_id, questao_id):
    with db.get_conn() as conn:
        return conn.execute(
            "SELECT * FROM revisao_eventos WHERE usuario_id = ? AND questao_id = ? ORDER BY id",
            (usuario_id, questao_id),
        ).fetchall()


def test_cada_avaliacao_vira_um_evento_com_estado_antes_e_depois(usuario_teste, questao_teste):
    sr.registrar_revisao(questao_teste, 5, usuario_id=usuario_teste, origem="pratica",
                         correta=True, alternativa="A", tempo_ms=12000)
    sr.registrar_revisao(questao_teste, 4, usuario_id=usuario_teste, origem="revisao")

    primeiro, segundo = _eventos(usuario_teste, questao_teste)
    assert (primeiro["origem"], primeiro["correta"], primeiro["alternativa"], primeiro["tempo_ms"]) == ("pratica", 1, "A", 12000)
    assert primeiro["facilidade_antes"] is None and primeiro["atraso_dias"] is None
    assert primeiro["repeticoes_depois"] == 1 and primeiro["intervalo_depois"] == 1

    assert segundo["repeticoes_antes"] == 1 and segundo["intervalo_depois"] == 6
    assert segundo["facilidade_antes"] == primeiro["facilidade_depois"]
    assert segundo["correta"] is None  # sem alternativa: autoavaliação
    assert sr.obter_estado(questao_teste, usuario_id=usuario_teste)["proxima_revisao"] == segundo["proxima_revisao"]


def test_prazo_previsto_e_o_prazo_de_fato_agendado(usuario_teste, questao_teste):
    """Os botões da Revisão prometiam prazos fixos que o SM-2 não seguia."""
    for nota in [5, 3, 4, 1, 5, 5, 4]:
        estado = sr.obter_estado(questao_teste, usuario_id=usuario_teste)
        previsto = sr.prever_prazos(estado)[nota]
        antes = datetime.datetime.now()
        sr.registrar_revisao(questao_teste, nota, usuario_id=usuario_teste)
        agendado = sr.obter_estado(questao_teste, usuario_id=usuario_teste)["proxima_revisao"] - antes
        if "minutos" in previsto:
            assert abs(agendado.total_seconds() / 60 - previsto["minutos"]) < 1
        else:
            assert agendado.days == previsto["dias"]


def test_prazos_de_questao_nova_e_depois_de_dois_acertos(usuario_teste, questao_teste):
    assert sr.prever_prazos(None) == {1: {"minutos": 10}, 3: {"dias": 1}, 4: {"dias": 1}, 5: {"dias": 1}}
    sr.registrar_revisao(questao_teste, 5, usuario_id=usuario_teste)
    sr.registrar_revisao(questao_teste, 5, usuario_id=usuario_teste)
    estado = sr.obter_estado(questao_teste, usuario_id=usuario_teste)
    prazos = sr.prever_prazos(estado)
    assert prazos[1] == {"minutos": 10}
    assert prazos[4] == {"dias": round(6 * estado["facilidade"])}


def test_acertos_seguidos_param_no_teto_sem_estourar_a_data():
    """Sem teto, ~26 acertos seguidos levavam a próxima revisão para depois do
    ano 9999 e `datetime` levantava OverflowError."""
    agora = datetime.datetime.now()
    estado = None
    for _ in range(60):
        estado = sr.calcular_proximo_estado(estado, 5, agora)
    assert estado["intervalo_dias"] == sr.INTERVALO_MAXIMO_DIAS
    assert sr.prever_prazos(estado)[5] == {"dias": sr.INTERVALO_MAXIMO_DIAS}


def test_revisao_com_alternativa_errada_vira_nota_1_mesmo_se_mandarem_5(usuario_teste, questao_teste):
    r = sr.avaliar_revisao(questao_teste, 5, usuario_id=usuario_teste, alternativa="B", tempo_ms=5000)
    assert r["correta"] is False and r["qualidade"] == 1
    assert r["prazos"][1] == {"minutos": 10}
    evento = _eventos(usuario_teste, questao_teste)[-1]
    assert (evento["origem"], evento["qualidade"], evento["correta"], evento["alternativa"]) == ("revisao", 1, 0, "B")


def test_revisao_com_alternativa_certa_nao_aceita_nota_de_erro(usuario_teste, questao_teste):
    r = sr.avaliar_revisao(questao_teste, 1, usuario_id=usuario_teste, alternativa="A")
    assert r["correta"] is True and r["qualidade"] == 3


def test_atraso_registra_quanto_a_revisao_ja_tinha_vencido(usuario_teste, questao_teste):
    sr.registrar_revisao(questao_teste, 5, usuario_id=usuario_teste)
    with db.get_conn() as conn:
        conn.execute(
            "UPDATE revisao SET proxima_revisao = ? WHERE usuario_id = ? AND questao_id = ?",
            (datetime.datetime.now() - datetime.timedelta(days=2), usuario_teste, questao_teste),
        )
    sr.registrar_revisao(questao_teste, 4, usuario_id=usuario_teste)
    assert 1.9 < _eventos(usuario_teste, questao_teste)[-1]["atraso_dias"] < 2.1
