"""
"O que mudou": o id da última entrada lida fica na conta, não no navegador,
porque ela estuda no celular e no computador e o aviso apareceria duas vezes.
Este teste prende só a metade do servidor — a lista das entradas mora no front
(`frontend/src/lib/novidades.ts`), e o servidor de propósito não a conhece.
"""

import uuid

from fastapi.testclient import TestClient

from api.main import app

import db


def test_novidade_lida_fica_gravada_na_conta():
    email = f"pytest_nov_{uuid.uuid4().hex[:10]}@teste.local"
    try:
        with TestClient(app) as client:
            r = client.post("/auth/signup", json={"email": email, "senha": "senha123"})
            assert r.status_code == 201, r.text

            # Conta nova nunca viu nada: é o que faz a caixa aparecer.
            assert client.get("/me").json()["novidades_vistas"] is None

            assert client.patch("/me/novidades", json={"visto": "2026-09-23"}).status_code == 200
            assert client.get("/me").json()["novidades_vistas"] == "2026-09-23"

            # Uma entrega nova sobrescreve: "já viu" é sempre em relação a uma
            # entrada, senão a próxima novidade nunca apareceria.
            client.patch("/me/novidades", json={"visto": "2026-10-01"})
            assert client.get("/me").json()["novidades_vistas"] == "2026-10-01"
    finally:
        with db.get_conn() as conn:
            conn.execute("DELETE FROM usuarios WHERE email = ?", (email,))
