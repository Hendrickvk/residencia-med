import db


def test_filtro_por_area_encontra_a_questao(usuario_teste, area_teste, questao_teste):
    ids = db.ids_questoes_filtro_pratica(usuario_id=usuario_teste, area_id=area_teste)
    assert questao_teste in ids


def test_filtro_apenas_erros(usuario_teste, questao_teste):
    ids_antes = db.ids_questoes_filtro_pratica(usuario_id=usuario_teste, apenas_erros=True)
    assert questao_teste not in ids_antes

    db.registrar_resposta(questao_teste, "B", False, usuario_id=usuario_teste)

    ids_depois = db.ids_questoes_filtro_pratica(usuario_id=usuario_teste, apenas_erros=True)
    assert questao_teste in ids_depois


def test_filtro_excluir_respondidas(usuario_teste, questao_teste, area_teste):
    ids_antes = db.ids_questoes_filtro_pratica(
        usuario_id=usuario_teste, area_id=area_teste, excluir_respondidas=True,
    )
    assert questao_teste in ids_antes

    db.registrar_resposta(questao_teste, "A", True, usuario_id=usuario_teste)

    ids_depois = db.ids_questoes_filtro_pratica(
        usuario_id=usuario_teste, area_id=area_teste, excluir_respondidas=True,
    )
    assert questao_teste not in ids_depois


def test_obter_questoes_por_ids_embute_gabarito_e_estado_marcada(usuario_teste, questao_teste):
    resultado = db.obter_questoes_por_ids([questao_teste], usuario_id=usuario_teste)
    assert len(resultado) == 1
    q = resultado[0]
    assert q["id"] == questao_teste
    assert q["resposta_correta"] == "A"
    assert q["marcada"] is False


def test_obter_questoes_por_ids_reflete_estado_marcada(usuario_teste, questao_teste):
    db.marcar_questao(usuario_teste, questao_teste)
    resultado = db.obter_questoes_por_ids([questao_teste], usuario_id=usuario_teste)
    assert resultado[0]["marcada"] is True


def test_obter_questoes_por_ids_preserva_a_ordem_pedida(usuario_teste, area_teste):
    import datetime
    import json
    import uuid

    ids_criados = []
    with db.get_conn() as conn:
        c = conn.cursor()
        for _ in range(3):
            enunciado = f"[pytest {uuid.uuid4().hex[:8]}] ordem"
            c.execute("""
                INSERT INTO questoes
                    (area_id, subtopico_id, enunciado, alternativas, resposta_correta,
                     explicacao, banca, ano, criada_em)
                VALUES (?, NULL, ?, ?, 'A', '', 'PYTEST', 2024, ?)
            """, (area_teste, enunciado, json.dumps({"A": "x", "B": "y"}), datetime.datetime.now().isoformat()))
            ids_criados.append(c.lastrowid)
    try:
        ordem_invertida = list(reversed(ids_criados))
        resultado = db.obter_questoes_por_ids(ordem_invertida, usuario_id=usuario_teste)
        assert [q["id"] for q in resultado] == ordem_invertida
    finally:
        with db.get_conn() as conn:
            for qid in ids_criados:
                conn.execute("DELETE FROM questoes WHERE id = ?", (qid,))
