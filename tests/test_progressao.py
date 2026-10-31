"""
Progressão: as regras que protegem o diagnóstico e a contabilidade do razão
(progressao.py). O que a tela promete (`recompensa`) tem de ser o que entra no
razão, e nenhum reenvio pode pagar duas vezes.
"""

import datetime
import importlib.util
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import db
import progressao
import repeticao_espacada as sr
from api.main import app
from api.routers.simulados import criar_oficial as criar_oficial_endpoint
from api.routers.simulados import finalizar as finalizar_endpoint
from api.schemas import SimuladoOficialIn
from tests.conftest import confirmar_email


@pytest.fixture(autouse=True, scope="module")
def _tabelas_existem():
    db.init_db()


@pytest.fixture()
def conta_api():
    """Uma conta de verdade pela API. O e-mail é sorteado antes do `/auth/signup`,
    para o teardown apagar por e-mail mesmo que o endpoint quebre depois de inserir."""
    email = f"pytest_{uuid.uuid4().hex[:12]}@teste.local"
    with TestClient(app) as client:
        id_conta = client.post("/auth/signup", json={"email": email, "senha": "senha123"}).json()["id"]
        confirmar_email(id_conta)
        yield client
    with db.get_conn() as conn:
        conn.execute("DELETE FROM usuarios WHERE email = ?", (email,))


def _usuario(usuario_id):
    return {"id": usuario_id, "email": "pytest@teste.local"}


def _saldo(usuario_id):
    with db.get_conn() as conn:
        linha = conn.execute("SELECT xp_total, moedas FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return linha["xp_total"], linha["moedas"]


def _soma_razao(usuario_id):
    with db.get_conn() as conn:
        linha = conn.execute(
            "SELECT COALESCE(SUM(xp), 0) AS xp, COALESCE(SUM(moedas), 0) AS moedas "
            "FROM progresso_eventos WHERE usuario_id = ?",
            (usuario_id,),
        ).fetchone()
    return linha["xp"], linha["moedas"]


def _vencer(usuario_id, questao_id):
    """Põe a revisão da questão no passado, como se o prazo tivesse chegado."""
    with db.get_conn() as conn:
        conn.execute(
            "UPDATE revisao SET proxima_revisao = ? WHERE usuario_id = ? AND questao_id = ?",
            (db.agora_br() - datetime.timedelta(days=1), usuario_id, questao_id),
        )


def _ontem(usuario_id):
    """O que foi pago hoje passa a ter sido pago ontem: libera a questão de novo."""
    ontem = db.hoje_br() - datetime.timedelta(days=1)
    with db.get_conn() as conn:
        conn.execute(
            "UPDATE progresso_eventos SET dia = ?, chave = chave || ':ontem' WHERE usuario_id = ?",
            (ontem, usuario_id),
        )


# --- Regras puras -----------------------------------------------------------

def test_curva_de_niveis():
    assert progressao.nivel_de(0) == 1
    assert progressao.nivel_de(79) == 1
    assert progressao.nivel_de(80) == 2
    assert progressao.xp_do_nivel(10) == 2160
    assert progressao.nivel_de(2160) == 10
    assert progressao.nivel_de(2159) == 9


def test_progresso_diz_quanto_falta_e_a_proxima_patente():
    p = progressao.progresso_do_xp(4640)
    assert (p["nivel"], p["patente"], p["falta"], p["pct"]) == (14, "Internato", 120, 80.0)
    assert p["proxima_patente"] == {"nome": "R1", "nivel": 20}
    assert progressao.progresso_do_xp(10 ** 6)["proxima_patente"] is None


def test_patentes_em_cada_inicio():
    for inicio, nome in progressao.PATENTES:
        assert progressao.patente_de(inicio) == nome
    assert progressao.patente_de(4) == "Ciclo básico"
    assert progressao.patente_de(9) == "Ciclo clínico"


def test_nivel_de_area():
    assert progressao.progresso_da_area(0) == {"xp": 0, "nivel": 1, "falta": 100, "pct": 0.0}
    assert progressao.progresso_da_area(1420) == {"xp": 1420, "nivel": 5, "falta": 180, "pct": 70.0}
    assert progressao.progresso_da_area(7500)["nivel"] == 10
    assert progressao.progresso_da_area(99_999)["falta"] == 0


def test_tabela_de_xp_e_moedas():
    regra = progressao.regra_caso
    assert regra(primeira=True, vencida=False, correta=True) == (10, 1)
    assert regra(primeira=True, vencida=False, correta=False) == (5, 0)
    assert regra(primeira=False, vencida=True, correta=True) == (10, 1)
    assert regra(primeira=False, vencida=True, correta=False) == (5, 0)
    # Já vista e não vencida: a moeda não vem, e a nota não muda nada.
    assert regra(primeira=False, vencida=False, correta=True) == (2, 0)
    assert regra(primeira=False, vencida=False, correta=False) == (2, 0)


def test_prova_so_conta_com_90_por_cento_respondida():
    xp = progressao.xp_de_prova
    assert xp(bloco=None, num_questoes=100, respondidas=90) == 100
    assert xp(bloco=None, num_questoes=100, respondidas=89) == 0
    assert xp(bloco=2, num_questoes=25, respondidas=25) == 25
    assert xp(bloco=None, num_questoes=0, respondidas=0) == 0


# --- Pontuação nos fluxos ---------------------------------------------------

def test_primeira_resposta_certa_paga_e_vira_saldo(usuario_teste, questao_teste):
    novo = sr.registrar_revisao(questao_teste, 5, usuario_id=usuario_teste, origem="pratica", correta=True, alternativa="A")
    ganho = novo["ganho"]
    assert (ganho["xp"], ganho["moedas"]) == (10, 2)  # o dobro dos 10 primeiros acertos do dia
    assert list(ganho["areas"].values()) == [10]
    assert _saldo(usuario_teste) == (10, 2)
    assert _soma_razao(usuario_teste) == (10, 2)


def test_chute_rende_igual_ao_seguro(conta_api, quatro_questoes):
    """Pela API, com a marca de chute. Se rendesse menos, ela pararia de marcar, e
    a triagem e o SM-2 perderiam o dado."""
    seguro = conta_api.post("/respostas", json={
        "questao_id": quatro_questoes[0], "alternativa": "A", "confianca": "seguro",
    }).json()["ganho"]
    chute = conta_api.post("/respostas", json={
        "questao_id": quatro_questoes[1], "alternativa": "A", "confianca": "chute",
    }).json()["ganho"]
    assert (chute["xp"], chute["moedas"]) == (seguro["xp"], seguro["moedas"])


def test_erro_rende_xp_e_nenhuma_moeda(usuario_teste, questao_teste):
    ganho = sr.registrar_revisao(
        questao_teste, 1, usuario_id=usuario_teste, origem="pratica", correta=False, alternativa="B",
    )["ganho"]
    assert (ganho["xp"], ganho["moedas"]) == (5, 0)


def test_mesma_questao_so_paga_uma_vez_por_dia(usuario_teste, questao_teste):
    """Erro seguido de acerto (a revisão de 10 minutos depois) e o reenvio da fila
    caem aqui: o segundo não paga, e o saldo não anda."""
    primeiro = sr.registrar_revisao(
        questao_teste, 1, usuario_id=usuario_teste, origem="pratica", correta=False, alternativa="B",
    )
    assert primeiro["ganho"]["xp"] == 5
    _vencer(usuario_teste, questao_teste)
    segundo = sr.registrar_revisao(
        questao_teste, 5, usuario_id=usuario_teste, origem="revisao", correta=True, alternativa="A",
    )
    assert segundo["ganho"] is None
    assert _saldo(usuario_teste) == (5, 0)


def test_revisao_vencida_paga_como_questao_nova(usuario_teste, questao_teste):
    sr.registrar_revisao(questao_teste, 5, usuario_id=usuario_teste, origem="pratica", correta=True, alternativa="A")
    _ontem(usuario_teste)
    _vencer(usuario_teste, questao_teste)
    ganho = sr.registrar_revisao(
        questao_teste, 5, usuario_id=usuario_teste, origem="revisao", correta=True, alternativa="A",
    )["ganho"]
    assert ganho["xp"] == 10
    assert ganho["moedas"] > 0


def test_ja_vista_e_nao_vencida_rende_pouco_e_sem_moeda(usuario_teste, questao_teste):
    sr.registrar_revisao(questao_teste, 5, usuario_id=usuario_teste, origem="pratica", correta=True, alternativa="A")
    _ontem(usuario_teste)
    ganho = sr.registrar_revisao(
        questao_teste, 5, usuario_id=usuario_teste, origem="pratica", correta=True, alternativa="A",
    )["ganho"]
    assert (ganho["xp"], ganho["moedas"]) == (2, 0)


def test_sem_resposta_a_uma_alternativa_nao_paga(usuario_teste, questao_teste):
    """As telas antigas do Streamlit avaliam sem responder: não há o que pagar."""
    assert sr.registrar_revisao(questao_teste, 5, usuario_id=usuario_teste)["ganho"] is None
    assert _saldo(usuario_teste) == (0, 0)


def test_dobro_de_moedas_acaba_no_decimo_acerto_do_dia(usuario_teste, area_teste):
    agora = db.agora_br()
    with db.get_conn() as conn:
        for i in range(progressao.ACERTOS_EM_DOBRO_POR_DIA):
            conn.execute("""
                INSERT INTO progresso_eventos (usuario_id, chave, tipo, xp, moedas, dia, criado_em)
                VALUES (?, ?, 'caso', 10, 2, ?, ?)
            """, (usuario_teste, f"caso:{-i - 1}:{agora.date()}", agora.date(), agora))
        c = conn.cursor()
        c.execute("""
            INSERT INTO questoes (area_id, enunciado, alternativas, resposta_correta, criada_em)
            VALUES (?, ?, ?, 'A', ?)
        """, (area_teste, f"[pytest {uuid.uuid4().hex[:8]}] Questão de teste.", '{"A": "certa", "B": "errada"}', agora.isoformat()))
        questao_id = c.lastrowid
    ganho = sr.registrar_revisao(questao_id, 5, usuario_id=usuario_teste, origem="pratica", correta=True, alternativa="A")["ganho"]
    assert ganho["moedas"] == 1


def test_meta_de_revisao_paga_uma_vez_quando_cumprida(usuario_teste, quatro_questoes):
    with db.get_conn() as conn:
        conn.execute("UPDATE usuarios SET meta_revisao_diaria = 2 WHERE id = ?", (usuario_teste,))
    primeira = sr.avaliar_revisao(quatro_questoes[0], 5, usuario_id=usuario_teste, alternativa="A")
    assert primeira["ganho"]["xp"] == 10
    segunda = sr.avaliar_revisao(quatro_questoes[1], 5, usuario_id=usuario_teste, alternativa="A")
    assert segunda["ganho"]["xp"] == 10 + progressao.XP_META_REVISAO
    terceira = sr.avaliar_revisao(quatro_questoes[2], 5, usuario_id=usuario_teste, alternativa="A")
    assert terceira["ganho"]["xp"] == 10
    assert _saldo(usuario_teste)[0] == 30 + progressao.XP_META_REVISAO


def test_cartao_rende_pelo_mesmo_tanto_em_qualquer_nota(usuario_teste):
    pasta = db.criar_pasta(usuario_id=usuario_teste, nome="Pasta", cor=None)
    baralho = db.criar_baralho(usuario_id=usuario_teste, pasta_id=pasta, nome="Baralho")
    ganhos = []
    for nota in (1, 3, 4, 5):
        cartao = db.criar_cartao(usuario_id=usuario_teste, baralho_id=baralho, frente="f", verso="v")
        ganhos.append(sr.avaliar_cartao(cartao, nota, usuario_id=usuario_teste)["ganho"])
    assert {(g["xp"], g["moedas"]) for g in ganhos} == {(progressao.XP_CARTAO, 0)}


def test_mesmo_cartao_e_desfazer_nao_pagam_de_novo(usuario_teste):
    pasta = db.criar_pasta(usuario_id=usuario_teste, nome="Pasta", cor=None)
    baralho = db.criar_baralho(usuario_id=usuario_teste, pasta_id=pasta, nome="Baralho")
    cartao = db.criar_cartao(usuario_id=usuario_teste, baralho_id=baralho, frente="f", verso="v")
    assert sr.avaliar_cartao(cartao, 4, usuario_id=usuario_teste)["ganho"]["xp"] == progressao.XP_CARTAO
    db.desfazer_revisao_cartao(cartao, usuario_id=usuario_teste)
    assert sr.avaliar_cartao(cartao, 5, usuario_id=usuario_teste)["ganho"] is None
    assert _saldo(usuario_teste)[0] == progressao.XP_CARTAO


def test_teto_diario_de_cartoes(usuario_teste):
    agora = db.agora_br()
    with db.get_conn() as conn:
        conn.execute("""
            INSERT INTO progresso_eventos (usuario_id, chave, tipo, xp, dia, criado_em)
            SELECT ?, 'cartao:teste:' || n, 'cartao', ?, ?, ?
            FROM generate_series(1, ?) AS n
        """, (usuario_teste, progressao.XP_CARTAO, agora.date(), agora, progressao.TETO_CARTOES_PAGOS_DIA))
    pasta = db.criar_pasta(usuario_id=usuario_teste, nome="Pasta", cor=None)
    baralho = db.criar_baralho(usuario_id=usuario_teste, pasta_id=pasta, nome="Baralho")
    cartao = db.criar_cartao(usuario_id=usuario_teste, baralho_id=baralho, frente="f", verso="v")
    assert sr.avaliar_cartao(cartao, 4, usuario_id=usuario_teste)["ganho"] is None


def test_simulado_so_paga_ao_finalizar_e_uma_vez(usuario_teste, edicao_teste):
    banca, edicao, numeros = edicao_teste
    usuario = _usuario(usuario_teste)
    criado = criar_oficial_endpoint(SimuladoOficialIn(banca=banca, edicao=edicao), usuario=usuario)
    itens = db.listar_itens_simulado(criado["id"], usuario_id=usuario_teste)
    for item in itens:
        db.registrar_resposta_simulado(criado["id"], item["id"], "A", usuario_id=usuario_teste)
    # Responder a prova não rende nada: XP aqui vazaria o gabarito.
    assert _saldo(usuario_teste) == (0, 0)

    primeira = finalizar_endpoint(criado["id"], usuario=usuario)
    xp_esperado = len(numeros) * 10 + progressao.XP_PROVA_INTEIRA
    assert sum(g["xp"] for g in primeira["ganhos"]) == xp_esperado
    assert _saldo(usuario_teste)[0] == xp_esperado

    guardado = db.obter_simulado(criado["id"], usuario_id=usuario_teste)
    assert guardado["xp_ganho"] == xp_esperado

    assert finalizar_endpoint(criado["id"], usuario=usuario)["ganhos"] == []
    assert _saldo(usuario_teste)[0] == xp_esperado


def _idas_ao_finalizar(usuario_id, questoes, monkeypatch):
    """Quantas consultas o finalizar faz para um simulado com estas questões."""
    simulado_id = db.criar_simulado(None, None, len(questoes), 10, questoes, usuario_id=usuario_id)
    for q in questoes:
        db.registrar_resposta_simulado(simulado_id, q, "A", usuario_id=usuario_id)
    idas = []
    original = db._PGCursor.execute

    def contar(self, query, params=()):
        idas.append(query)
        return original(self, query, params)

    with monkeypatch.context() as m:
        m.setattr(db._PGCursor, "execute", contar)
        finalizar_endpoint(simulado_id, usuario=_usuario(usuario_id))
    return len(idas)


def test_finalizar_nao_cresce_com_o_tamanho_da_prova(usuario_teste, quatro_questoes, questao_teste, monkeypatch):
    """Do servidor ao Neon são 14 ms por ida. A uma ida por questão (eram 10), uma
    prova de 100 levava 15 s para finalizar; em lote, o número é fixo."""
    uma = _idas_ao_finalizar(usuario_teste, [questao_teste], monkeypatch)
    quatro = _idas_ao_finalizar(usuario_teste, quatro_questoes, monkeypatch)
    assert uma == quatro


def test_finalizar_em_lote_grava_o_mesmo_que_uma_a_uma(usuario_teste, quatro_questoes):
    """O histórico e o SM-2 de uma prova têm de sair iguais aos de quem respondeu no
    Praticar: é o que o Painel e a Revisão leem."""
    certa, errada, em_branco, ja_vista = quatro_questoes
    sr.registrar_revisao(ja_vista, 5, usuario_id=usuario_teste, origem="pratica", correta=True, alternativa="A")
    simulado_id = db.criar_simulado(None, None, 4, 10, quatro_questoes, usuario_id=usuario_teste)
    db.registrar_resposta_simulado(simulado_id, certa, "A", usuario_id=usuario_teste)
    db.registrar_resposta_simulado(simulado_id, errada, "B", usuario_id=usuario_teste)
    db.registrar_resposta_simulado(simulado_id, ja_vista, "A", usuario_id=usuario_teste)
    db.somar_tempo_simulado(simulado_id, certa, 4000, usuario_id=usuario_teste)
    finalizar_endpoint(simulado_id, usuario=_usuario(usuario_teste))

    with db.get_conn() as conn:
        respostas = conn.execute(
            "SELECT questao_id, resposta_dada, correta, tempo_ms FROM respostas WHERE usuario_id = ? AND questao_id = ANY(?)",
            (usuario_teste, [certa, errada, em_branco]),
        ).fetchall()
        eventos = conn.execute(
            "SELECT questao_id, origem, qualidade, correta, alternativa, tempo_ms, facilidade_antes, atraso_dias "
            "FROM revisao_eventos WHERE usuario_id = ? AND origem = 'simulado'",
            (usuario_teste,),
        ).fetchall()
        estados = {
            r["questao_id"]: r
            for r in conn.execute("SELECT * FROM revisao WHERE usuario_id = ?", (usuario_teste,)).fetchall()
        }
    assert {(r["questao_id"], r["resposta_dada"], r["correta"], r["tempo_ms"]) for r in respostas} == {
        (certa, "A", 1, 4000), (errada, "B", 0, None),
    }
    por_questao = {e["questao_id"]: e for e in eventos}
    assert set(por_questao) == {certa, errada, ja_vista}
    assert (por_questao[certa]["qualidade"], por_questao[certa]["correta"]) == (5, 1)
    assert (por_questao[errada]["qualidade"], por_questao[errada]["correta"]) == (1, 0)
    assert por_questao[certa]["facilidade_antes"] is None
    assert por_questao[ja_vista]["facilidade_antes"] is not None
    assert por_questao[ja_vista]["atraso_dias"] is not None
    # O erro volta em 10 minutos, o acerto amanhã: quem calcula é o mesmo SM-2.
    assert em_branco not in estados
    assert estados[errada]["proxima_revisao"] < estados[certa]["proxima_revisao"]
    assert estados[ja_vista]["repeticoes"] == 2


def test_prova_refeita_nao_paga_o_bonus_de_novo(usuario_teste, edicao_teste):
    banca, edicao, numeros = edicao_teste
    usuario = _usuario(usuario_teste)
    for _ in range(2):
        criado = criar_oficial_endpoint(SimuladoOficialIn(banca=banca, edicao=edicao), usuario=usuario)
        for item in db.listar_itens_simulado(criado["id"], usuario_id=usuario_teste):
            db.registrar_resposta_simulado(criado["id"], item["id"], "A", usuario_id=usuario_teste)
        finalizar_endpoint(criado["id"], usuario=usuario)
    # A segunda vez, no mesmo dia, não paga nem as questões nem a prova.
    assert _saldo(usuario_teste)[0] == len(numeros) * 10 + progressao.XP_PROVA_INTEIRA


# --- O que a tela promete ---------------------------------------------------

def test_previsao_e_o_que_entra_no_razao(usuario_teste, quatro_questoes):
    nova, vencida, ja_vista, paga = quatro_questoes
    for q in (vencida, ja_vista, paga):
        sr.registrar_revisao(q, 5, usuario_id=usuario_teste, origem="pratica", correta=True, alternativa="A")
    _ontem(usuario_teste)
    _vencer(usuario_teste, vencida)
    sr.registrar_revisao(paga, 5, usuario_id=usuario_teste, origem="pratica", correta=True, alternativa="A")

    previsao = progressao.prever_casos(quatro_questoes, usuario_id=usuario_teste)
    assert previsao[nova] == {"certo": 10, "errado": 5}
    assert previsao[vencida] == {"certo": 10, "errado": 5}
    assert previsao[ja_vista] == {"certo": 2, "errado": 2}
    assert previsao[paga] == {"certo": 0, "errado": 0}

    for q in (nova, vencida, ja_vista):
        ganho = sr.registrar_revisao(q, 5, usuario_id=usuario_teste, origem="pratica", correta=True, alternativa="A")["ganho"]
        assert ganho["xp"] == previsao[q]["certo"]


def test_saldo_e_a_soma_do_razao(usuario_teste, quatro_questoes):
    for i, q in enumerate(quatro_questoes):
        correta = i % 2 == 0
        sr.registrar_revisao(
            q, 5 if correta else 1, usuario_id=usuario_teste, origem="pratica", correta=correta,
            alternativa="A" if correta else "B",
        )
    assert _saldo(usuario_teste) == _soma_razao(usuario_teste)


def test_virada_do_dia_no_relogio_de_brasilia(usuario_teste, questao_teste, monkeypatch):
    """Às 22h30 de Brasília ainda é hoje, e não amanhã, como seria em UTC."""
    noite = datetime.datetime(2026, 10, 31, 22, 30)
    monkeypatch.setattr(db, "agora_br", lambda: noite)
    sr.registrar_revisao(questao_teste, 5, usuario_id=usuario_teste, origem="pratica", correta=True, alternativa="A")
    with db.get_conn() as conn:
        linha = conn.execute("SELECT dia, chave FROM progresso_eventos WHERE usuario_id = ?", (usuario_teste,)).fetchone()
    assert linha["dia"] == datetime.date(2026, 10, 31)
    assert linha["chave"].endswith("2026-10-31")


def test_troca_de_patente_vem_marcada(usuario_teste, questao_teste):
    with db.get_conn() as conn:
        conn.execute(
            "UPDATE usuarios SET xp_total = ? WHERE id = ?", (progressao.xp_do_nivel(20) - 5, usuario_teste),
        )
    ganho = sr.registrar_revisao(questao_teste, 5, usuario_id=usuario_teste, origem="pratica", correta=True, alternativa="A")["ganho"]
    assert ganho["trocou_patente"] is True
    assert ganho["depois"]["patente"] == "R1"


# --- API --------------------------------------------------------------------

def test_me_e_pagina_de_progresso(conta_api, area_teste, quatro_questoes):
    client = conta_api
    r = client.get("/praticar/sessao", params={"area_id": area_teste, "quantidade": 4})
    assert r.status_code == 200
    assert r.json()["questoes"][0]["recompensa"] == {"certo": 10, "errado": 5}

    assert client.get("/me").json()["progresso"]["nivel"] == 1
    for q in quatro_questoes:
        assert client.post("/respostas", json={"questao_id": q, "alternativa": "A"}).status_code == 200
    me = client.get("/me").json()
    assert me["progresso"]["xp"] == 40
    assert me["moedas"] == 8

    r = client.get("/progresso")
    assert r.status_code == 200
    dados = r.json()
    assert dados["nivel"]["xp"] == 40
    area = next(a for a in dados["areas"] if a["id"] == area_teste)
    assert area["xp"] == 40
    # As cinco grandes áreas aparecem mesmo sem XP.
    assert sum(1 for a in dados["areas"] if a["nome"] in db.TAXONOMIA) == 5
    assert dados["dias"] == [{"dia": db.hoje_br().isoformat(), "xp": 40}]
    assert dados["maior_sequencia"] == 1


def test_progresso_exige_sessao():
    with TestClient(app) as client:
        assert client.get("/progresso").status_code == 401


# --- O script que refaz o histórico -----------------------------------------

_spec = importlib.util.spec_from_file_location(
    "retroagir_progresso", Path(__file__).resolve().parent.parent / "scripts" / "retroagir_progresso.py",
)
retroagir = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(retroagir)


def _areas_e_usuario(conn, usuario_id):
    areas = {q["id"]: q["area_id"] for q in conn.execute("SELECT id, area_id FROM questoes").fetchall()}
    return areas, conn.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()


def test_script_chega_ao_mesmo_saldo_do_jogo_ao_vivo(usuario_teste, quatro_questoes, edicao_teste):
    """A garantia do script: refazer o histórico dá o que o jogo pagou. Cobre erro,
    acerto, repetição no dia, cartão, meta e prova."""
    banca, edicao, _ = edicao_teste
    usuario = _usuario(usuario_teste)
    with db.get_conn() as conn:
        conn.execute("UPDATE usuarios SET meta_revisao_diaria = 1 WHERE id = ?", (usuario_teste,))
    certa, errada, repetida, revisada = quatro_questoes
    sr.registrar_revisao(certa, 5, usuario_id=usuario_teste, origem="pratica", correta=True, alternativa="A")
    sr.registrar_revisao(errada, 1, usuario_id=usuario_teste, origem="pratica", correta=False, alternativa="B")
    sr.registrar_revisao(repetida, 5, usuario_id=usuario_teste, origem="pratica", correta=True, alternativa="A")
    sr.registrar_revisao(repetida, 5, usuario_id=usuario_teste, origem="pratica", correta=True, alternativa="A")
    sr.avaliar_revisao(revisada, 5, usuario_id=usuario_teste, alternativa="A")

    pasta = db.criar_pasta(usuario_id=usuario_teste, nome="Pasta", cor=None)
    baralho = db.criar_baralho(usuario_id=usuario_teste, pasta_id=pasta, nome="Baralho")
    cartao = db.criar_cartao(usuario_id=usuario_teste, baralho_id=baralho, frente="f", verso="v")
    sr.avaliar_cartao(cartao, 4, usuario_id=usuario_teste)

    criado = criar_oficial_endpoint(SimuladoOficialIn(banca=banca, edicao=edicao), usuario=usuario)
    for item in db.listar_itens_simulado(criado["id"], usuario_id=usuario_teste):
        db.registrar_resposta_simulado(criado["id"], item["id"], "A", usuario_id=usuario_teste)
    finalizar_endpoint(criado["id"], usuario=usuario)

    ao_vivo = _saldo(usuario_teste)
    assert ao_vivo[0] > 0
    with db.get_conn() as conn:
        conn.execute("DELETE FROM progresso_eventos WHERE usuario_id = ?", (usuario_teste,))
        conn.execute("UPDATE usuarios SET xp_total = 0, moedas = 0 WHERE id = ?", (usuario_teste,))
        areas, linha = _areas_e_usuario(conn, usuario_teste)
        assert retroagir.retroagir_conta(conn, linha, areas)
    assert _saldo(usuario_teste) == ao_vivo


def test_script_e_idempotente(usuario_teste, questao_teste):
    sr.registrar_revisao(questao_teste, 5, usuario_id=usuario_teste, origem="pratica", correta=True, alternativa="A")
    saldo = _saldo(usuario_teste)
    with db.get_conn() as conn:
        areas, linha = _areas_e_usuario(conn, usuario_teste)
        assert retroagir.retroagir_conta(conn, linha, areas) == []
    assert _saldo(usuario_teste) == saldo


def test_script_paga_resposta_anterior_aos_eventos():
    """Antes de `revisao_eventos` existir, a resposta só está em `respostas`."""
    quando = datetime.datetime(2026, 9, 8, 10, 0)
    linhas = retroagir.lancamentos_de_casos(
        [], [{"questao_id": 7, "correta": 1, "respondida_em": quando.isoformat()}], {7: 3},
    )
    assert [(li["chave"], li["xp"], li["moedas"], li["area_id"]) for li in linhas] == [
        ("caso:7:2026-09-08", 10, 2, 3),
    ]


def test_script_nao_conta_resposta_e_evento_duas_vezes():
    quando = datetime.datetime(2026, 9, 28, 10, 0)
    evento = {
        "questao_id": 7, "origem": "pratica", "correta": 1, "atraso_dias": None,
        "facilidade_antes": None, "registrado_em": quando,
    }
    linhas = retroagir.lancamentos_de_casos(
        [evento], [{"questao_id": 7, "correta": 1, "respondida_em": quando.isoformat()}], {7: 3},
    )
    assert len(linhas) == 1
