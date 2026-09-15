"""
Testes da Fase 5 do MIGRACAO.md: gabarito não pode vazar num simulado em
andamento, e o estado "marcada" (dívida do redesign em Streamlit) precisa
estar disponível pra sustentar o terceiro estado da grade de navegação.
Também cobre o simulado por edição oficial (ordem do caderno, tempo no
ritmo oficial), a retomada de simulado em andamento, o tempo por questão, as
provas oficiais feitas e os temas para revisar.

Chama as funções dos routers diretamente (sem TestClient/HTTP) passando
`usuario=` explícito — os fixtures de usuário não têm senha em texto plano
pra fazer login de verdade via `/auth/login`, e aqui o que importa é a
lógica do endpoint, não a autenticação (já coberta em test_api_smoke.py).
"""

import datetime

import db
from api.routers.simulados import criar_oficial as criar_oficial_endpoint
from api.routers.simulados import desempenho as desempenho_endpoint
from api.routers.simulados import disponiveis as disponiveis_endpoint
from api.routers.simulados import edicoes as edicoes_endpoint
from api.routers.simulados import em_andamento as em_andamento_endpoint
from api.routers.simulados import finalizar as finalizar_endpoint
from api.routers.simulados import itens as itens_endpoint
from api.routers.simulados import somar_tempo as tempo_endpoint
from api.routers.simulados import temas_errados as temas_endpoint
from api.schemas import SimuladoOficialIn, TempoSimuladoIn


def _usuario(usuario_id):
    return {"id": usuario_id, "email": "pytest@teste.local"}


def test_itens_simulado_nao_vaza_gabarito_antes_de_finalizar(usuario_teste, questao_teste):
    simulado_id = db.criar_simulado(None, None, 1, 10, [questao_teste], usuario_id=usuario_teste)

    payload_antes = itens_endpoint(simulado_id, usuario=_usuario(usuario_teste))
    assert payload_antes[0]["id"] == questao_teste
    assert "resposta_correta" not in payload_antes[0]
    assert "explicacao" not in payload_antes[0]

    finalizar_endpoint(simulado_id, usuario=_usuario(usuario_teste))

    payload_depois = itens_endpoint(simulado_id, usuario=_usuario(usuario_teste))
    assert payload_depois[0]["resposta_correta"] == "A"


def test_listar_itens_simulado_inclui_estado_marcada(usuario_teste, questao_teste):
    simulado_id = db.criar_simulado(None, None, 1, 10, [questao_teste], usuario_id=usuario_teste)

    itens = db.listar_itens_simulado(simulado_id, usuario_id=usuario_teste)
    assert itens[0]["marcada"] is False

    db.marcar_questao(usuario_teste, questao_teste)
    itens = db.listar_itens_simulado(simulado_id, usuario_id=usuario_teste)
    assert itens[0]["marcada"] is True


def test_disponiveis_conta_questoes_sem_filtro(usuario_teste):
    resultado = disponiveis_endpoint(area_id=None, banca=None, usuario=_usuario(usuario_teste))
    assert resultado["total"] >= 1


def test_edicoes_lista_edicao_com_total_e_tempo_oficial(usuario_teste, edicao_teste):
    banca, edicao, _ = edicao_teste
    lista = edicoes_endpoint(usuario=_usuario(usuario_teste))
    encontrada = next(e for e in lista if e["banca"] == banca and e["edicao"] == edicao)
    assert encontrada["total"] == 3
    assert encontrada["tempo_limite_min"] == 3 * db.MINUTOS_POR_QUESTAO_PROVA_OFICIAL


def test_simulado_oficial_segue_ordem_do_caderno_sem_vazar_gabarito(usuario_teste, edicao_teste):
    banca, edicao, numeros_inseridos = edicao_teste
    criado = criar_oficial_endpoint(SimuladoOficialIn(banca=banca, edicao=edicao), usuario=_usuario(usuario_teste))

    simulado = db.obter_simulado(criado["id"], usuario_id=usuario_teste)
    assert simulado["edicao"] == edicao
    assert simulado["num_questoes"] == 3
    assert simulado["tempo_limite_min"] == 3 * db.MINUTOS_POR_QUESTAO_PROVA_OFICIAL

    itens = itens_endpoint(criado["id"], usuario=_usuario(usuario_teste))
    assert [i["numero_prova"] for i in itens] == sorted(numeros_inseridos)
    assert all("resposta_correta" not in i for i in itens)


def test_questao_de_duas_provas_entra_nas_duas_com_o_numero_de_cada_caderno(usuario_teste, edicao_teste):
    banca, edicao, _ = edicao_teste
    outra_banca, outra_edicao = "PYTEST-OUTRA", f"{edicao}-b"
    questao_id = db.ids_questoes_da_edicao(banca, edicao)[0]  # a de número 5 no caderno original
    with db.get_conn() as conn:
        conn.execute(
            "INSERT INTO questoes_provas (questao_id, banca, edicao, numero_prova) VALUES (?, ?, ?, 77)",
            (questao_id, outra_banca, outra_edicao),
        )
    usuario = _usuario(usuario_teste)

    outra = criar_oficial_endpoint(SimuladoOficialIn(banca=outra_banca, edicao=outra_edicao), usuario=usuario)
    assert [(i["id"], i["numero_prova"]) for i in itens_endpoint(outra["id"], usuario=usuario)] == [(questao_id, 77)]

    original = criar_oficial_endpoint(SimuladoOficialIn(banca=banca, edicao=edicao), usuario=usuario)
    assert itens_endpoint(original["id"], usuario=usuario)[0]["numero_prova"] == 5

    assert db.contar_questoes_disponiveis(None, outra_banca) == 1
    assert db.ids_questoes_filtro_pratica(usuario_id=usuario_teste, banca=outra_banca) == [questao_id]


def test_em_andamento_ignora_finalizado_e_tempo_esgotado(usuario_teste, questao_teste):
    usuario = _usuario(usuario_teste)
    assert em_andamento_endpoint(usuario=usuario) is None

    simulado_id = db.criar_simulado(None, None, 1, 10, [questao_teste], usuario_id=usuario_teste)
    db.registrar_resposta_simulado(simulado_id, questao_teste, "B", usuario_id=usuario_teste)
    atual = em_andamento_endpoint(usuario=usuario)
    assert atual["id"] == simulado_id
    assert atual["respondidas"] == 1

    # Começou há 20 minutos com limite de 10: tempo esgotado, não é retomável.
    vinte_min_atras = (datetime.datetime.now() - datetime.timedelta(minutes=20)).isoformat()
    with db.get_conn() as conn:
        conn.execute("UPDATE simulados SET iniciado_em = ? WHERE id = ?", (vinte_min_atras, simulado_id))
    assert em_andamento_endpoint(usuario=usuario) is None

    outro_id = db.criar_simulado(None, None, 1, 10, [questao_teste], usuario_id=usuario_teste)
    finalizar_endpoint(outro_id, usuario=usuario)
    assert em_andamento_endpoint(usuario=usuario) is None


def test_tempo_por_questao_soma_as_passagens_ate_finalizar(usuario_teste, questao_teste):
    usuario = _usuario(usuario_teste)
    simulado_id = db.criar_simulado(None, None, 1, 10, [questao_teste], usuario_id=usuario_teste)
    for ms in (40_000, 25_000):
        tempo_endpoint(simulado_id, TempoSimuladoIn(questao_id=questao_teste, tempo_ms=ms), usuario=usuario)
    db.somar_tempo_simulado(simulado_id, questao_teste, 99_000, usuario_id=-1)  # não é o dono
    db.registrar_resposta_simulado(simulado_id, questao_teste, "A", usuario_id=usuario_teste)
    finalizar_endpoint(simulado_id, usuario=usuario)
    db.somar_tempo_simulado(simulado_id, questao_teste, 99_000, usuario_id=usuario_teste)  # já finalizado

    assert itens_endpoint(simulado_id, usuario=usuario)[0]["tempo_ms"] == 65_000
    # O tempo segue para o histórico de respostas, como no Praticar.
    with db.get_conn() as conn:
        resposta = conn.execute(
            "SELECT tempo_ms FROM respostas WHERE usuario_id = ? AND questao_id = ?", (usuario_teste, questao_teste)
        ).fetchone()
    assert resposta["tempo_ms"] == 65_000


def test_provas_oficiais_feitas_contam_as_questoes_ja_vistas(usuario_teste, edicao_teste):
    banca, edicao, _ = edicao_teste
    usuario = _usuario(usuario_teste)
    vista = db.ids_questoes_da_edicao(banca, edicao)[0]
    db.registrar_resposta(vista, "A", True, usuario_id=usuario_teste)  # no Praticar, antes da prova
    criado = criar_oficial_endpoint(SimuladoOficialIn(banca=banca, edicao=edicao), usuario=usuario)
    db.registrar_resposta_simulado(criado["id"], vista, "A", usuario_id=usuario_teste)
    assert db.simulados_oficiais_feitos(usuario_id=usuario_teste) == []  # ainda em andamento

    finalizar_endpoint(criado["id"], usuario=usuario)
    [feita] = db.simulados_oficiais_feitos(usuario_id=usuario_teste)
    assert (feita["edicao"], feita["acertos"], feita["num_questoes"], feita["ja_vistas"]) == (edicao, 1, 3, 1)


def test_temas_para_revisar_so_depois_de_finalizar(usuario_teste, quatro_questoes):
    usuario = _usuario(usuario_teste)
    ids = quatro_questoes[:3]
    with db.get_conn() as conn:
        tema = conn.execute(
            "SELECT id FROM subtopicos WHERE origem IS NULL AND especialidade_id IS NOT NULL ORDER BY id LIMIT 1"
        ).fetchone()["id"]
        for questao_id in ids:
            conn.execute("UPDATE questoes SET subtopico_id = ? WHERE id = ?", (tema, questao_id))
    simulado_id = db.criar_simulado(None, None, 3, 10, ids, usuario_id=usuario_teste)
    db.registrar_resposta_simulado(simulado_id, ids[0], "A", usuario_id=usuario_teste)
    db.registrar_resposta_simulado(simulado_id, ids[1], "B", usuario_id=usuario_teste)
    # Durante a prova, acerto por tema ou por área entregaria o gabarito.
    assert temas_endpoint(simulado_id, usuario=usuario) == []
    assert desempenho_endpoint(simulado_id, usuario=usuario) == []

    finalizar_endpoint(simulado_id, usuario=usuario)
    [t] = temas_endpoint(simulado_id, usuario=usuario)
    assert (t["subtopico_id"], t["total"], t["acertos"]) == (tema, 3, 1)
    assert desempenho_endpoint(simulado_id, usuario=usuario)[0]["acertos"] == 1
