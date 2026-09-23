"""
Nome e cor do avatar. O que este teste prende é a validação da cor: o valor vem
do cliente e vira CSS na tela, então cor fora da lista tem que cair no padrão
em vez de passar direto.
"""

import uuid

from fastapi.testclient import TestClient

from api.main import app

import db


def test_nome_e_cor_gravam_e_cor_invalida_cai_no_padrao():
    email = f"pytest_perfil_{uuid.uuid4().hex[:10]}@teste.local"
    try:
        with TestClient(app) as client:
            assert client.post("/auth/signup", json={"email": email, "senha": "senha123"}).status_code == 201

            me = client.get("/me").json()
            assert me["nome"] is None
            assert me["cor_perfil"] == db.COR_PERFIL_PADRAO

            client.patch("/me/perfil", json={"nome": "  Beatriz  ", "cor": "ameixa"})
            me = client.get("/me").json()
            assert me["nome"] == "Beatriz", "o nome tem que chegar sem os espaços das pontas"
            assert me["cor_perfil"] == "ameixa"

            # Cor fora da lista não vira CSS: volta ao padrão.
            client.patch("/me/perfil", json={"nome": "Beatriz", "cor": "roxo"})
            assert client.get("/me").json()["cor_perfil"] == db.COR_PERFIL_PADRAO

            # Valor longo nem chega ao banco: o schema recusa antes.
            r = client.patch("/me/perfil", json={"nome": "Beatriz", "cor": "red; background: url(x)"})
            assert r.status_code == 422

            # Nome em branco volta a NULL, e a tela mostra o e-mail de novo.
            client.patch("/me/perfil", json={"nome": "   ", "cor": "rosa"})
            me = client.get("/me").json()
            assert me["nome"] is None
            assert me["cor_perfil"] == "rosa"

            # Nome comprido é cortado, não recusado.
            client.patch("/me/perfil", json={"nome": "G" * db.LIMITE_NOME, "cor": "rosa"})
            assert len(client.get("/me").json()["nome"]) == db.LIMITE_NOME
    finally:
        with db.get_conn() as conn:
            conn.execute("DELETE FROM usuarios WHERE email = ?", (email,))
