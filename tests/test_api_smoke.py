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
