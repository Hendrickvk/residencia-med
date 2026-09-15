"""
Domínio no Painel (só a primeira resposta a cada questão) e prioridades de
estudo (`db.priorizar_temas`): peso do tema nos cadernos do INEP × o que falta
de domínio estimado.
"""

import db


def _tentativa(correta, tema, area=1, especialidade=10):
    return {"area_id": area, "especialidade_id": especialidade, "subtopico_id": tema, "correta": correta}


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


def test_painel_conta_so_a_primeira_resposta(usuario_teste, area_teste, questao_teste):
    db.registrar_resposta(questao_teste, "B", False, usuario_id=usuario_teste)
    db.registrar_resposta(questao_teste, "A", True, usuario_id=usuario_teste)

    [area] = db.desempenho_dashboard_combinado(usuario_id=usuario_teste)["por_area"]
    assert (area["area_id"], area["total"], area["acertos"]) == (area_teste, 1, 0)
    [dia] = db.evolucao_diaria(usuario_id=usuario_teste)
    assert (dia["total"], dia["acertos"]) == (1, 0)


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
