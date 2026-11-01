"""
As conquistas (conquistas.py): conquista paga duas vezes, secreta vazada e
conquista ganha sem ter feito a coisa são o que este arquivo impede.
"""

import datetime
import json
import threading
import uuid

import pytest
from fastapi.testclient import TestClient

import conquistas
import db
import progressao
from api.main import app
from tests.conftest import confirmar_email

D = datetime.date(2026, 10, 1)


def _dia(n):
    return D + datetime.timedelta(days=n)


@pytest.fixture(autouse=True, scope="module")
def _tabelas_existem():
    db.init_db()


def _responder(usuario_id, questao_id, correta):
    with db.get_conn() as conn:
        conn.execute(
            "INSERT INTO respostas (usuario_id, questao_id, resposta_dada, correta, respondida_em) VALUES (?, ?, 'A', ?, ?)",
            (usuario_id, questao_id, int(correta), db.agora_br().isoformat()),
        )


def _saldo(usuario_id):
    with db.get_conn() as conn:
        return conn.execute("SELECT moedas FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()["moedas"]


def test_ids_unicos_e_medidas_que_existem():
    ids = [c["id"] for c in conquistas.CONQUISTAS]
    assert len(ids) == len(set(ids))
    for c in conquistas.CONQUISTAS:
        assert c["grau"] in conquistas.ORDEM_GRAU and 10 <= c["moedas"] <= 300
        # Toda conquista não secreta diz o que falta.
        assert c["secreta"] or c["nota"] or c["dica"]


def test_maior_ofensiva_com_dia_protegido():
    estudo = {_dia(0), _dia(1), _dia(3), _dia(10)}
    # O dia 2, protegido, liga as duas pontas e não conta.
    assert conquistas.maior_ofensiva(estudo, {_dia(2)}) == 3
    assert conquistas.maior_ofensiva(estudo, set()) == 2
    assert conquistas.maior_ofensiva(set(), set()) == 0


def test_maior_ausencia_e_sequencia_certa():
    assert conquistas.maior_ausencia({_dia(0), _dia(1), _dia(40)}) == 39
    assert conquistas.maior_ausencia({_dia(0)}) == 0
    assert conquistas.maior_sequencia_certa([1, 1, 0, 1, 1, 1, 0]) == 3


def test_trajetoria_saiu_da_emergencia_e_uma_historia():
    # 20 respostas com 25%: em Emergência. Depois acerta até passar de 40%.
    tentativas = [("Cirurgia", 1 if i % 4 == 0 else 0) for i in range(20)]
    assert conquistas.trajetoria_da_triagem(tentativas)["saiu_emergencia"] == 0
    tentativas += [("Cirurgia", 1)] * 10
    marcos = conquistas.trajetoria_da_triagem(tentativas)
    assert marcos["saiu_emergencia"] == 1
    # Quem nunca esteve em Emergência não "saiu" dela.
    assert conquistas.trajetoria_da_triagem([("Cirurgia", 1)] * 30)["saiu_emergencia"] == 0


def test_trajetoria_exige_volume_e_ignora_area_de_fora():
    assert conquistas.trajetoria_da_triagem([("Cirurgia", 1)] * 19)["areas_verdes_max"] == 0
    assert conquistas.trajetoria_da_triagem([("Cirurgia", 1)] * 20)["areas_azuis_max"] == 1
    assert conquistas.trajetoria_da_triagem([("__pytest_area", 1)] * 50)["areas_verdes_max"] == 0


def test_cinco_areas_no_verde_precisam_ser_ao_mesmo_tempo():
    tentativas = [(area, 1) for area in db.TAXONOMIA for _ in range(20)]
    marcos = conquistas.trajetoria_da_triagem(tentativas)
    assert marcos["areas_verdes_max"] == 5 and marcos["sem_vermelho"] == 1 and marcos["areas_azuis_max"] == 5
    # A primeira área despenca antes de a última chegar ao volume.
    primeira, *resto = db.TAXONOMIA
    tentativas = [(primeira, 1)] * 20 + [(primeira, 0)] * 40 + [(a, 1) for a in resto for _ in range(20)]
    assert conquistas.trajetoria_da_triagem(tentativas)["areas_verdes_max"] == 4


def test_prova_em_branco_nao_conta():
    feita = {"banca": "USP", "edicao": "2026", "em_blocos": False, "num_questoes": 100, "corte": None}
    assert conquistas.medidas_de_provas([feita], set(), [{"banca": "USP", "edicao": "2026"}])["provas"] == 0
    medidas = conquistas.medidas_de_provas(
        [feita], {progressao.chave_prova("USP", "2026", None)}, [{"banca": "USP", "edicao": "2026"}],
    )
    assert medidas["provas"] == 1 and medidas["banca:USP"] == 1 and medidas["provas_pct"] == 100


def test_prova_em_blocos_precisa_de_todos_os_blocos_pagos():
    feita = {"banca": "ENAMED", "edicao": "2025", "em_blocos": True, "num_questoes": 50, "corte": None}
    um = {progressao.chave_prova("ENAMED", "2025", 1)}
    assert conquistas.medidas_de_provas([feita], um, [])["provas_em_blocos"] == 0
    dois = um | {progressao.chave_prova("ENAMED", "2025", 2)}
    assert conquistas.medidas_de_provas([feita], dois, [])["provas_em_blocos"] == 1


def test_conquista_paga_uma_vez_so_no_razao(usuario_teste, questao_teste):
    _responder(usuario_teste, questao_teste, True)
    antes = _saldo(usuario_teste)
    novas = conquistas.verificar(usuario_teste)
    ids = {n["id"] for n in novas}
    assert "casos-1" in ids and "certos-10" not in ids
    assert _saldo(usuario_teste) == antes + sum(n["moedas"] for n in novas)
    assert conquistas.verificar(usuario_teste) == []
    assert _saldo(usuario_teste) == antes + sum(n["moedas"] for n in novas)
    with db.get_conn() as conn:
        soma = conn.execute(
            "SELECT COALESCE(SUM(moedas), 0) AS m FROM progresso_eventos WHERE usuario_id = ?", (usuario_teste,),
        ).fetchone()["m"]
    assert soma == _saldo(usuario_teste)


def test_duas_avaliacoes_ao_mesmo_tempo_pagam_uma(usuario_teste, questao_teste):
    _responder(usuario_teste, questao_teste, True)
    resultados = []
    linhas = [threading.Thread(target=lambda: resultados.append(conquistas.verificar(usuario_teste))) for _ in range(2)]
    for t in linhas:
        t.start()
    for t in linhas:
        t.join()
    pagos = [n["id"] for r in resultados for n in r]
    assert pagos.count("casos-1") == 1


def test_secreto_nao_vaza_antes_de_acontecer():
    email = f"pytest_{uuid.uuid4().hex[:12]}@teste.local"
    try:
        with TestClient(app) as client:
            id_conta = client.post("/auth/signup", json={"email": email, "senha": "senha123"}).json()["id"]
            confirmar_email(id_conta)
            resposta = client.get("/progresso/conquistas")
            assert resposta.status_code == 200
            corpo = resposta.text
            for c in conquistas.CONQUISTAS:
                if c["secreta"]:
                    assert c["nome"] not in corpo and c["id"] not in corpo
            dados = json.loads(corpo)
            assert dados["obtidos"] == 0 and dados["total"] == len(conquistas.CONQUISTAS)
            assert sum(s["qtd"] for s in dados["series"]) == dados["total"]
            assert dados["series"][0]["itens"][0]["nota"] == "0 de 3 dias"
    finally:
        with db.get_conn() as conn:
            conn.execute("DELETE FROM usuarios WHERE email = ?", (email,))


def test_rotas_exigem_sessao():
    with TestClient(app) as client:
        assert client.get("/progresso/conquistas").status_code == 401
        assert client.post("/progresso/verificar").status_code == 401


def test_vitrine_vem_do_maior_grau(usuario_teste):
    agora = db.agora_br()
    with db.get_conn() as conn:
        for id_conquista in ("casos-1", "ofensiva-7", "ofensiva-60", "revisao-1"):
            progressao._lancar(conn, usuario_id=usuario_teste, chave=conquistas.chave(id_conquista), tipo="conquista",
                               xp=0, moedas=1, area_id=None, agora=agora)
    vitrine = conquistas.vitrine(usuario_teste)
    assert vitrine["obtidos"] == 4
    assert [i["id"] for i in vitrine["itens"]][:2] == ["ofensiva-60", "ofensiva-7"] and len(vitrine["itens"]) == 3
