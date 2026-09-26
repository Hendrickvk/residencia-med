"""
Tela "Uso da plataforma" do admin (db.metricas_uso) e os erros que o app manda
(db.registrar_erro_front). As contas de teste saem das métricas por padrão, então
os testes pedem `excluir_testes=False` para enxergar a própria conta.
"""

import db


def _conta(metricas, usuario_id):
    return next(c for c in metricas["por_conta"] if c["id"] == usuario_id)


def test_metricas_contam_resposta_revisao_e_cartao(usuario_teste, questao_teste):
    import repeticao_espacada as sr

    db.registrar_resposta(questao_teste, "A", True, usuario_id=usuario_teste)
    sr.registrar_revisao(questao_teste, 4, usuario_id=usuario_teste, origem="revisao", correta=True, alternativa="A")
    pasta = db.criar_pasta(usuario_id=usuario_teste, nome="Pasta", cor="azul-5")
    baralho = db.criar_baralho(usuario_id=usuario_teste, pasta_id=pasta, nome="Baralho")
    cartao = db.criar_cartao(usuario_id=usuario_teste, baralho_id=baralho, frente="F", verso="V")
    sr.avaliar_cartao(cartao, 4, usuario_id=usuario_teste)

    conta = _conta(db.metricas_uso(excluir_testes=False), usuario_teste)
    assert (conta["respostas"], conta["revisoes"], conta["cartoes"]) == (1, 1, 1)
    assert conta["dias_ativos"] == 1
    assert conta["ultima_atividade"] is not None


def test_conta_de_teste_fica_fora_por_padrao(usuario_teste, questao_teste):
    db.registrar_resposta(questao_teste, "A", True, usuario_id=usuario_teste)
    assert all(c["id"] != usuario_teste for c in db.metricas_uso()["por_conta"])


def test_erro_do_app_fica_guardado_e_tem_teto_por_hora(usuario_teste):
    assert db.registrar_erro_front(usuario_id=usuario_teste, mensagem="Quebrou no Painel", url="/painel")
    recentes = db.erros_front_recentes()
    assert any(e["mensagem"] == "Quebrou no Painel" and e["url"] == "/painel" for e in recentes)

    for _ in range(db.LIMITE_ERROS_FRONT_POR_HORA - 1):
        db.registrar_erro_front(usuario_id=usuario_teste, mensagem="laço")
    assert db.registrar_erro_front(usuario_id=usuario_teste, mensagem="laço") is False
