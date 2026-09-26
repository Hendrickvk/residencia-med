import datetime

import db
import repeticao_espacada as sr


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


def test_revisao_de_casos_conta_na_ofensiva(usuario_teste, questao_teste):
    # A Revisão grava só em `revisao_eventos`, sem passar por `respostas`.
    sr.registrar_revisao(questao_teste, 4, usuario_id=usuario_teste, origem="revisao", correta=True, alternativa="A")
    assert db.calcular_ofensiva(usuario_id=usuario_teste) == (1, True)


def test_cartao_avaliado_conta_na_ofensiva(usuario_teste):
    pasta = db.criar_pasta(usuario_id=usuario_teste, nome="Pasta", cor="azul-5")
    baralho = db.criar_baralho(usuario_id=usuario_teste, pasta_id=pasta, nome="Baralho")
    cartao = db.criar_cartao(usuario_id=usuario_teste, baralho_id=baralho, frente="Frente", verso="Verso")
    agora = datetime.datetime.now()
    db.gravar_revisao_cartao(
        cartao, usuario_id=usuario_teste, qualidade=4, estado_antes=None, agora=agora,
        estado_depois={"facilidade": 2.5, "intervalo_dias": 1, "repeticoes": 1,
                       "proxima_revisao": agora + datetime.timedelta(days=1)},
    )
    assert db.calcular_ofensiva(usuario_id=usuario_teste) == (1, True)


def test_ofensiva_quebra_com_um_dia_de_buraco(usuario_teste, questao_teste):
    anteontem = (datetime.date.today() - datetime.timedelta(days=2)).isoformat()
    db.registrar_resposta(questao_teste, "A", True, usuario_id=usuario_teste)
    with db.get_conn() as conn:
        conn.execute("UPDATE respostas SET respondida_em = ? WHERE usuario_id = ?", (anteontem, usuario_teste))
    dias, respondeu_hoje = db.calcular_ofensiva(usuario_id=usuario_teste)
    assert dias == 0
    assert respondeu_hoje is False
