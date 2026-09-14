"""
Evolução (fase 3): estágios dos casos, retenção por bloco de 7 dias e por
especialidade, recuperados e consolidados — tudo definido em
`repeticao_espacada.classificar_eventos`.
"""

import datetime

import db
import repeticao_espacada as sr

AGORA = datetime.datetime.now()


def _agendar(usuario_id, questao_id, proxima, *, repeticoes=1, intervalo=6, facilidade=2.5):
    with db.get_conn() as conn:
        conn.execute("""
            INSERT INTO revisao (usuario_id, questao_id, facilidade, intervalo_dias, repeticoes, proxima_revisao)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (usuario_id, questao_id, facilidade, intervalo, repeticoes, proxima))


def _relogio(monkeypatch, momento):
    """Avaliações gravadas "no passado": o SM-2 e o evento usam `_agora`."""
    monkeypatch.setattr(sr, "_agora", lambda: momento)


def test_estagios_saem_do_estado_atual(usuario_teste, quatro_questoes):
    aprendendo, consolidando, consolidado, _ = quatro_questoes
    _agendar(usuario_teste, aprendendo, AGORA, repeticoes=0, intervalo=1)
    _agendar(usuario_teste, consolidando, AGORA, repeticoes=3, intervalo=20)
    _agendar(usuario_teste, consolidado, AGORA, repeticoes=4, intervalo=21)
    assert sr.estagios_casos(usuario_id=usuario_teste) == {"aprendendo": 1, "consolidando": 1, "consolidado": 1}


def test_refazer_logo_depois_do_erro_nao_mede_memoria_e_lembrar_no_dia_seguinte_recupera(
    usuario_teste, questao_teste, monkeypatch
):
    inicio = AGORA - datetime.timedelta(days=10)
    _relogio(monkeypatch, inicio)
    sr.registrar_revisao(questao_teste, 1, usuario_id=usuario_teste, origem="pratica", correta=False, alternativa="B")
    _relogio(monkeypatch, inicio + datetime.timedelta(minutes=12))
    refeito = sr.avaliar_revisao(questao_teste, 4, usuario_id=usuario_teste, alternativa="A")
    assert refeito["recuperado"] is False  # 12 minutos: memória de curto prazo

    _relogio(monkeypatch, inicio + datetime.timedelta(days=1, hours=1))
    assert sr.avaliar_revisao(questao_teste, 4, usuario_id=usuario_teste, alternativa="A")["recuperado"] is True

    # Recuperado conta uma vez: o teste seguinte é só um acerto.
    _relogio(monkeypatch, inicio + datetime.timedelta(days=7, hours=2))
    assert sr.avaliar_revisao(questao_teste, 4, usuario_id=usuario_teste, alternativa="A")["recuperado"] is False

    _relogio(monkeypatch, AGORA)
    semanas = sr.evolucao_memoria(usuario_id=usuario_teste)["semanas"]
    # Dia 1 (há 9 dias) no bloco anterior, dia 7 (há 3 dias) no atual; o
    # refeito de 12 minutos em nenhum.
    assert [(s["testes"], s["lembrou"]) for s in semanas[-2:]] == [(1, 1), (1, 1)]
    assert sum(s["testes"] for s in semanas) == 2


def test_erro_de_antes_do_historico_tambem_conta_como_recuperado(usuario_teste, questao_teste):
    # Estado de revisão sem nenhum evento: errou antes de existir o histórico.
    _agendar(usuario_teste, questao_teste, AGORA - datetime.timedelta(days=2), repeticoes=0, intervalo=1)
    r = sr.avaliar_revisao(questao_teste, 3, usuario_id=usuario_teste, alternativa="A")
    assert (r["recuperado"], r["consolidou"]) == (True, False)


def test_consolida_quando_o_intervalo_chega_a_21_dias(usuario_teste, questao_teste):
    _agendar(usuario_teste, questao_teste, AGORA - datetime.timedelta(days=1), repeticoes=3, intervalo=15)
    r = sr.avaliar_revisao(questao_teste, 4, usuario_id=usuario_teste, alternativa="A")
    assert r["intervalo_dias"] == 38 and r["consolidou"] is True and r["recuperado"] is False

    memoria = sr.evolucao_memoria(usuario_id=usuario_teste)
    assert memoria["estagios"] == {"aprendendo": 0, "consolidando": 0, "consolidado": 1}
    assert (memoria["ultimos_7_dias"]["consolidados"], memoria["ultimos_7_dias"]["testes"]) == (1, 1)


def test_retencao_por_bloco_de_7_dias_e_por_especialidade(usuario_teste, area_teste, quatro_questoes, monkeypatch):
    a, b, c, d = quatro_questoes
    with db.get_conn() as conn:
        conn.execute("INSERT INTO especialidades (area_id, nome) VALUES (?, '__pytest_especialidade')", (area_teste,))
        especialidade = conn.execute(
            "SELECT id FROM especialidades WHERE area_id = ?", (area_teste,)
        ).fetchone()["id"]
        conn.execute("UPDATE questoes SET especialidade_id = ? WHERE id IN (?, ?)", (especialidade, a, b))
    for questao_id in quatro_questoes:
        _agendar(usuario_teste, questao_id, AGORA - datetime.timedelta(days=30))

    for questao_id, dias_atras, lembrou in [(a, 10, False), (b, 2, False), (c, 2, True), (d, 0, True)]:
        _relogio(monkeypatch, AGORA - datetime.timedelta(days=dias_atras))
        sr.registrar_revisao(questao_id, 4 if lembrou else 1, usuario_id=usuario_teste, origem="revisao", correta=lembrou)

    _relogio(monkeypatch, AGORA)
    memoria = sr.evolucao_memoria(usuario_id=usuario_teste)
    assert len(memoria["semanas"]) == sr.SEMANAS_EVOLUCAO
    assert memoria["semanas"][-1]["inicio"] == (AGORA.date() - datetime.timedelta(days=6)).isoformat()
    assert [(s["testes"], s["lembrou"]) for s in memoria["semanas"][-2:]] == [(1, 0), (3, 2)]
    assert memoria["ultimos_7_dias"] == {
        "testes": 3, "lembrou": 2, "recuperados": 0, "consolidados": 0, "dias_com_revisao": 2,
    }
    assert [(e["especialidade"], e["testes"], e["lembrou"]) for e in memoria["especialidades"]] == [
        ("__pytest_especialidade", 2, 0),
        (None, 2, 2),
    ]


def test_sem_historico_tudo_zerado(usuario_teste):
    memoria = sr.evolucao_memoria(usuario_id=usuario_teste)
    assert memoria["especialidades"] == [] and all(s["testes"] == 0 for s in memoria["semanas"])
    assert memoria["ultimos_7_dias"]["dias_com_revisao"] == 0
