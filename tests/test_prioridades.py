"""
Domínio no Painel (só a primeira resposta a cada questão, com o chute valendo
meio), prioridades de
estudo (`db.priorizar_temas`: peso do tema nos cadernos do INEP × o que falta
de domínio estimado) e desempenho por tipo de pergunta.
"""

import datetime

import db


def _tentativa(pontos, tema, area=1, especialidade=10):
    return {"area_id": area, "especialidade_id": especialidade, "subtopico_id": tema, "pontos": pontos}


def _tema(tema, questoes_provas, area=1, especialidade=10):
    return {"subtopico_id": tema, "area_id": area, "especialidade_id": especialidade,
            "questoes_provas": questoes_provas, "tema": f"tema {tema}"}


def test_estimativa_parte_da_referencia_e_se_aproxima_do_resultado():
    assert db.estimar_dominio(0, 0, 0.6) == 0.6
    # Uma resposta certa não vira 100%.
    assert 0.5 < db.estimar_dominio(1, 1, 0.5) < 0.6
    assert db.estimar_dominio(90, 100, 0.5) > 0.85


def test_sem_respostas_nao_ha_prioridade():
    assert db.priorizar_temas([], [_tema(100, 10)], 100) == []


def test_prioridade_e_peso_na_prova_vezes_lacuna():
    tentativas = [_tentativa(0, 100)] * 5 + [_tentativa(1, 200)] * 5 + [_tentativa(0, 300)] * 5
    temas = [_tema(100, 10), _tema(200, 10), _tema(300, 2)]
    ordem = [p["subtopico_id"] for p in db.priorizar_temas(tentativas, temas, 100)]
    # Mesmo peso: vem antes quem erra mais. Errar tudo num tema que quase não cai fica por último.
    assert ordem == [100, 200, 300]


def test_tema_nunca_respondido_herda_a_especialidade():
    tentativas = [_tentativa(1, 100)] * 4 + [_tentativa(0, 100)]
    por_tema = {p["subtopico_id"]: p for p in db.priorizar_temas(tentativas, [_tema(100, 5), _tema(200, 5)], 50)}
    area = db.estimar_dominio(4, 5, 4 / 5)
    especialidade = db.estimar_dominio(4, 5, area)
    assert por_tema[200]["respondidas"] == 0
    assert por_tema[200]["dominio_estimado"] == round(100 * especialidade, 1)


def test_nota_projetada_pesa_os_temas_pela_prova():
    # Acerta tudo no tema 100 e erra tudo no 200.
    tentativas = [_tentativa(1, 100)] * 10 + [_tentativa(0, 200)] * 10
    igual = db.projetar_nota(tentativas, [_tema(100, 5), _tema(200, 5)])
    pesado = db.projetar_nota(tentativas, [_tema(100, 15), _tema(200, 5)])
    assert igual["minimo"] < igual["nota"] == 50 < igual["maximo"]
    assert pesado["nota"] > igual["nota"]
    assert db.projetar_nota([], [_tema(100, 5)]) is None


def test_margem_da_nota_diminui_mas_nao_some():
    temas = [_tema(100, 5), _tema(200, 5)]
    poucas = db.projetar_nota([_tentativa(1, 100), _tentativa(0, 200)] * 10, temas)
    muitas = db.projetar_nota([_tentativa(1, 100), _tentativa(0, 200)] * 500, temas)
    assert muitas["maximo"] - muitas["minimo"] < poucas["maximo"] - poucas["minimo"]
    # Sobra a variação de uma prova de 100 questões: perto de 10 pontos para cada lado.
    assert muitas["maximo"] - muitas["minimo"] > 19


def test_painel_conta_so_a_primeira_resposta(usuario_teste, area_teste, questao_teste):
    db.registrar_resposta(questao_teste, "B", False, usuario_id=usuario_teste)
    db.registrar_resposta(questao_teste, "A", True, usuario_id=usuario_teste)

    [area] = db.desempenho_dashboard_combinado(usuario_id=usuario_teste)["por_area"]
    assert (area["area_id"], area["total"], area["acertos"]) == (area_teste, 1, 0)
    [dia] = db.evolucao_diaria(usuario_id=usuario_teste)
    assert (dia["total"], dia["acertos"]) == (1, 0)


def test_acerto_no_chute_vale_meio(usuario_teste, questao_teste):
    with db.get_conn() as conn:
        conn.execute("UPDATE questoes SET tipo_pergunta = 'Conduta' WHERE id = ?", (questao_teste,))
    db.registrar_resposta(questao_teste, "A", True, usuario_id=usuario_teste, confianca="chute")

    [area] = db.desempenho_dashboard_combinado(usuario_id=usuario_teste)["por_area"]
    assert (area["total"], area["acertos"], area["pct_acerto"]) == (1, 0.5, 50)
    [dia] = db.evolucao_diaria(usuario_id=usuario_teste)
    assert (dia["total"], dia["acertos"]) == (1, 0.5)
    conduta = next(t for t in db.desempenho_por_tipo(usuario_id=usuario_teste) if t["tipo"] == "Conduta")
    assert (conduta["total"], conduta["acertos"]) == (1, 0.5)


def test_prioridades_estudo_usam_os_cadernos_do_inep(usuario_teste, questao_teste):
    assert db.prioridades_estudo(usuario_id=usuario_teste) == []

    db.registrar_resposta(questao_teste, "A", True, usuario_id=usuario_teste)
    prioridades = db.prioridades_estudo(usuario_id=usuario_teste)
    assert len(prioridades) == 3
    for p in prioridades:
        # A questão de teste não tem tema: nenhum tema real foi respondido.
        assert p["respondidas"] == 0
        assert 1 <= p["provas"] <= p["total_provas"]
        assert 0 < p["peso_prova"] <= 100


def test_semana_comeca_na_segunda():
    quarta = datetime.datetime(2026, 9, 16, 15, 30)
    assert db._inicio_da_semana(quarta) == datetime.datetime(2026, 9, 14)


def test_progresso_da_semana_separa_o_antes_do_depois(usuario_teste, quatro_questoes):
    antiga, nova = quatro_questoes[:2]
    with db.get_conn() as conn:
        tema = conn.execute(
            "SELECT id FROM subtopicos WHERE origem IS NULL AND especialidade_id IS NOT NULL ORDER BY id LIMIT 1"
        ).fetchone()["id"]
        for questao_id in (antiga, nova):
            conn.execute("UPDATE questoes SET subtopico_id = ? WHERE id = ?", (tema, questao_id))
    db.registrar_resposta(antiga, "A", True, usuario_id=usuario_teste)
    with db.get_conn() as conn:
        conn.execute(
            "UPDATE respostas SET respondida_em = ? WHERE usuario_id = ? AND questao_id = ?",
            ((db._inicio_da_semana() - datetime.timedelta(days=1)).isoformat(), usuario_teste, antiga),
        )
    db.registrar_resposta(nova, "B", False, usuario_id=usuario_teste)

    semana = db.progresso_semana(usuario_id=usuario_teste)
    assert (semana["novas"], semana["acertos"]) == (1, 0)
    [t] = semana["temas"]
    assert (t["subtopico_id"], t["novas"], t["testes"]) == (tema, 1, 0)
    # O acerto da semana passada é o "antes"; o erro desta semana derruba o "agora".
    assert t["dominio_antes"] > t["dominio_agora"]


def test_nota_projetada_do_aluno(usuario_teste, questao_teste):
    assert db.nota_projetada(usuario_id=usuario_teste) is None

    db.registrar_resposta(questao_teste, "A", True, usuario_id=usuario_teste)
    nota = db.nota_projetada(usuario_id=usuario_teste)
    # A questão de teste não tem tema: todo tema herda o acerto geral, de 100%.
    assert (nota["respondidas"], nota["nota"], nota["maximo"]) == (1, 100, 100)


def test_desempenho_por_tipo_conta_a_primeira_resposta(usuario_teste, questao_teste):
    with db.get_conn() as conn:
        conn.execute("UPDATE questoes SET tipo_pergunta = 'Conduta' WHERE id = ?", (questao_teste,))
    db.registrar_resposta(questao_teste, "A", True, usuario_id=usuario_teste)
    db.registrar_resposta(questao_teste, "B", False, usuario_id=usuario_teste)

    por_tipo = db.desempenho_por_tipo(usuario_id=usuario_teste)
    assert [t["tipo"] for t in por_tipo] == list(db.TIPOS_PERGUNTA)
    assert {t["tipo"]: (t["total"], t["acertos"]) for t in por_tipo} == {
        "Diagnóstico": (0, 0), "Exames": (0, 0), "Conduta": (1, 1), "Conceitos": (0, 0),
    }


def test_filtro_por_tipo_em_praticar(usuario_teste, questao_teste):
    with db.get_conn() as conn:
        conn.execute("UPDATE questoes SET tipo_pergunta = 'Exames' WHERE id = ?", (questao_teste,))
    assert questao_teste in db.ids_questoes_filtro_pratica(usuario_id=usuario_teste, tipo_pergunta="Exames")
    assert questao_teste not in db.ids_questoes_filtro_pratica(usuario_id=usuario_teste, tipo_pergunta="Conduta")
