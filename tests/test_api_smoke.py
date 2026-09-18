"""
Teste de integração de ponta a ponta: cadastra usuário via API, pede uma
sessão de prática e responde uma questão — o caminho que o critério de
sucesso do MIGRACAO.md §0 (feedback instantâneo) depende. Não substitui os
testes unitários do SM-2 (`test_sm2.py`); serve para pegar erro de fiação
entre routers/deps/schemas que só aparece com a app inteira montada.
"""

import uuid

from fastapi.testclient import TestClient

from api.main import app

import db


def test_fluxo_signup_sessao_e_resposta(area_teste, questao_teste):
    email = f"pytest_api_{uuid.uuid4().hex[:10]}@teste.local"
    usuario_id = None
    try:
        with TestClient(app) as client:
            r = client.post("/auth/signup", json={"email": email, "senha": "senha123"})
            assert r.status_code == 201, r.text
            usuario_id = r.json()["id"]

            r = client.get("/me")
            assert r.status_code == 200, r.text
            assert r.json()["email"] == email

            r = client.get("/praticar/sessao", params={"area_id": area_teste, "quantidade": 5})
            assert r.status_code == 200, r.text
            questoes = r.json()["questoes"]
            assert any(q["id"] == questao_teste for q in questoes)
            alvo = next(q for q in questoes if q["id"] == questao_teste)
            assert alvo["resposta_correta"] == "A"
            assert alvo["marcada"] is False
            assert alvo["alternativas"] == {"A": "certa", "B": "errada"}

            r = client.post("/respostas", json={
                "questao_id": questao_teste, "alternativa": "A", "confianca": "seguro",
            })
            assert r.status_code == 200, r.text
            assert r.json() == {"correta": True, "resposta_correta": "A"}

            r = client.get("/revisao/leva")
            assert r.status_code == 200, r.text

            r = client.post("/auth/logout")
            assert r.status_code == 200

            r = client.get("/me")
            assert r.status_code == 401
    finally:
        if usuario_id is not None:
            with db.get_conn() as conn:
                conn.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))


def test_endpoint_protegido_sem_sessao_retorna_401():
    with TestClient(app) as client:
        r = client.get("/me")
        assert r.status_code == 401


def test_contagem_bate_com_a_sessao_e_reage_aos_filtros(area_teste, quatro_questoes):
    """A contagem do Configurador é a promessa que a sessão tem de cumprir:
    se ela contar por um caminho diferente do que monta a fila, mente na
    primeira mudança de filtro."""
    email = f"pytest_api_{uuid.uuid4().hex[:10]}@teste.local"
    usuario_id = None
    try:
        with TestClient(app) as client:
            r = client.post("/auth/signup", json={"email": email, "senha": "senha123"})
            assert r.status_code == 201, r.text
            usuario_id = r.json()["id"]

            recorte = {"area_id": area_teste}
            r = client.get("/praticar/contagem", params=recorte)
            assert r.status_code == 200, r.text
            assert r.json() == {"total": 4}

            # Pedindo mais do que existe, a sessão devolve exatamente a contagem.
            r = client.get("/praticar/sessao", params={**recorte, "quantidade": 50})
            assert len(r.json()["questoes"]) == 4

            r = client.post("/respostas", json={
                "questao_id": quatro_questoes[0], "alternativa": "A", "confianca": "seguro",
            })
            assert r.status_code == 200, r.text

            r = client.get("/praticar/contagem", params={**recorte, "excluir_respondidas": True})
            assert r.json() == {"total": 3}
            r = client.get("/praticar/contagem", params={**recorte, "apenas_erros": True})
            assert r.json() == {"total": 0}
            r = client.get("/praticar/contagem", params={**recorte, "banca": "NAO_EXISTE"})
            assert r.json() == {"total": 0}
    finally:
        if usuario_id is not None:
            with db.get_conn() as conn:
                conn.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
