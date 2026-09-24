"""
A brincadeira de boas-vindas só sai do servidor para a própria conta.

O roteiro é pessoal e saiu do bundle em 2026-09-24 justamente para não chegar
ao navegador de qualquer visitante (HISTORICO.md, 2026-09-24). Se o `/me` o
devolvesse a outra conta, o texto voltaria a estar à vista de quem se
cadastrasse — e o cadastro é aberto.
"""

import uuid

from fastapi.testclient import TestClient

from api.main import app

import db

ROTEIRO = [{"tipo": "fala", "linhas": ["conexão nova no sistema."]}, {"tipo": "veredito"}]


def test_brincadeira_so_sai_para_a_propria_conta():
    dona = f"pytest_brinc_{uuid.uuid4().hex[:10]}@teste.local"
    outra = f"pytest_brinc_{uuid.uuid4().hex[:10]}@teste.local"
    try:
        with TestClient(app) as client:
            assert client.post("/auth/signup", json={"email": dona, "senha": "senha123"}).status_code == 201
            db.gravar_brincadeira(db.obter_usuario_por_email(dona)["id"], ROTEIRO, ["de novo."])
            assert client.get("/me").json()["brincadeira"] == {"roteiro": ROTEIRO, "reprise": ["de novo."]}

            # O cadastro troca o cookie: daqui em diante quem pergunta é a outra.
            assert client.post("/auth/signup", json={"email": outra, "senha": "senha123"}).status_code == 201
            assert client.get("/me").json()["brincadeira"] is None
    finally:
        with db.get_conn() as conn:
            conn.execute("DELETE FROM usuarios WHERE email IN (?, ?)", (dona, outra))
