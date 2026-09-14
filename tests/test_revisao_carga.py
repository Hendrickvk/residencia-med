"""
Carga sob controle (fase 2): prioridade da fila, meta diária, "revisar mais",
estimativa de tempo e previsão dos próximos dias.
"""

import datetime

import db
import repeticao_espacada as sr


def _agendar(usuario_id, questao_id, proxima, *, repeticoes=1, intervalo=6, facilidade=2.5):
    with db.get_conn() as conn:
        conn.execute("""
            INSERT INTO revisao (usuario_id, questao_id, facilidade, intervalo_dias, repeticoes, proxima_revisao)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (usuario_id, questao_id, facilidade, intervalo, repeticoes, proxima))


def _dias(n):
    return datetime.datetime.now() + datetime.timedelta(days=n)


def test_fila_prioriza_reaprendizado_depois_marcadas_depois_atraso_relativo(usuario_teste, quatro_questoes):
    reaprendendo, muito_atrasada, pouco_atrasada, marcada = quatro_questoes
    _agendar(usuario_teste, pouco_atrasada, _dias(-3), repeticoes=3, intervalo=30)
    _agendar(usuario_teste, muito_atrasada, _dias(-3), repeticoes=2, intervalo=2)
    _agendar(usuario_teste, reaprendendo, _dias(-0.001), repeticoes=0, intervalo=1)
    _agendar(usuario_teste, marcada, _dias(4), repeticoes=2, intervalo=6)
    db.marcar_questao(usuario_teste, marcada)

    ids = [q["id"] for q in sr.fila_revisao(usuario_id=usuario_teste)]
    assert ids == [reaprendendo, marcada, muito_atrasada, pouco_atrasada]


def test_meta_diaria_corta_a_fila_e_a_contagem_bate(usuario_teste, quatro_questoes):
    for questao_id in quatro_questoes:
        _agendar(usuario_teste, questao_id, _dias(-1))

    plano = sr.plano_revisao(usuario_id=usuario_teste, meta=2)
    assert (len(plano["fila"]), plano["excedente"], plano["feitas_hoje"]) == (2, 2, 0)
    assert sr.resumo_revisao_hoje(usuario_id=usuario_teste, meta=2)["hoje"] == 2

    sr.avaliar_revisao(plano["fila"][0]["id"], 4, usuario_id=usuario_teste, alternativa="A")
    plano = sr.plano_revisao(usuario_id=usuario_teste, meta=2)
    assert (plano["feitas_hoje"], len(plano["fila"]), plano["excedente"]) == (1, 1, 2)
    resumo = sr.resumo_revisao_hoje(usuario_id=usuario_teste, meta=2)
    assert (resumo["hoje"], resumo["excedente"]) == (1, 2)


def test_revisar_mais_libera_casos_alem_da_meta_sem_mudar_a_meta(usuario_teste, quatro_questoes):
    for questao_id in quatro_questoes:
        _agendar(usuario_teste, questao_id, _dias(-1))
    for q in sr.plano_revisao(usuario_id=usuario_teste, meta=2)["fila"]:
        sr.avaliar_revisao(q["id"], 4, usuario_id=usuario_teste, alternativa="A")

    assert sr.plano_revisao(usuario_id=usuario_teste, meta=2)["fila"] == []
    mais = sr.plano_revisao(usuario_id=usuario_teste, meta=2, extra=10)
    assert (len(mais["fila"]), mais["excedente"]) == (2, 0)


def test_praticar_nao_consome_a_meta_de_revisao(usuario_teste, questao_teste):
    sr.registrar_revisao(questao_teste, 5, usuario_id=usuario_teste, origem="pratica")
    assert sr.revisadas_hoje(usuario_id=usuario_teste) == 0
    sr.avaliar_revisao(questao_teste, 4, usuario_id=usuario_teste, alternativa="B")
    sr.avaliar_revisao(questao_teste, 4, usuario_id=usuario_teste, alternativa="A")
    assert sr.revisadas_hoje(usuario_id=usuario_teste) == 1  # errou e refez: um caso


def _revisar_com_tempo(usuario_id, questao_id, tempos_ms):
    for ms in tempos_ms:
        sr.registrar_revisao(questao_id, 4, usuario_id=usuario_id, origem="revisao", tempo_ms=ms)


def test_tempo_por_caso_ignora_tempos_implausiveis_e_usa_a_mediana(usuario_teste, questao_teste):
    assert sr.segundos_por_caso(usuario_id=usuario_teste) == sr.SEGUNDOS_POR_CASO_PADRAO
    plausiveis = [s * 1000 for s in range(20, 71, 5)]  # 11 tempos de 20 a 70 s: mediana 45 s
    # Cliques de teste e aba esquecida: se contassem, a mediana cairia para 42 s.
    _revisar_com_tempo(usuario_teste, questao_teste, plausiveis + [2_000, 2_000, 2_000, 1_200_000, 1_200_000])
    assert sr.segundos_por_caso(usuario_id=usuario_teste) == 45


def test_tempo_por_caso_com_poucas_medidas_plausiveis_usa_o_padrao(usuario_teste, questao_teste):
    # Parecido com o banco em 2026-09-13: muitos cliques rápidos, poucas leituras de verdade.
    _revisar_com_tempo(usuario_teste, questao_teste, [4_000] * 20 + [25_000] * 6)
    assert sr.segundos_por_caso(usuario_id=usuario_teste) == sr.SEGUNDOS_POR_CASO_PADRAO


def test_previsao_empurra_o_que_passa_da_meta_para_o_dia_seguinte(usuario_teste, quatro_questoes):
    a, b, c, d = quatro_questoes
    for questao_id in (a, b, c):
        _agendar(usuario_teste, questao_id, _dias(-1))
    amanha_meio_dia = datetime.datetime.combine(datetime.date.today() + datetime.timedelta(days=1), datetime.time(12))
    _agendar(usuario_teste, d, amanha_meio_dia)

    dias = sr.previsao_revisoes(usuario_id=usuario_teste, meta=2)
    assert len(dias) == 7 and dias[0]["dia"] == datetime.date.today().isoformat()
    assert (dias[0]["vencem"], dias[0]["dentro_meta"], dias[0]["acima_meta"]) == (3, 2, 1)
    assert (dias[1]["vencem"], dias[1]["dentro_meta"], dias[1]["acima_meta"]) == (1, 2, 0)
    assert all(x["dentro_meta"] + x["acima_meta"] == 0 for x in dias[2:])
