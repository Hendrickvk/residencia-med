"""
Força bruta no login. O que este teste prende é que errar a senha muitas vezes
para a mesma conta deixa de ser grátis — e que acertar limpa a conta, senão o
aluno que erra a senha três vezes e acerta na quarta pagaria por isso depois.
"""

import sys
import uuid

from fastapi.testclient import TestClient

from api.main import app
from api.routers import auth

import db


def _conta(client):
    email = f"pytest_login_{uuid.uuid4().hex[:10]}@teste.local"
    r = client.post("/auth/signup", json={"email": email, "senha": "senha12345"})
    assert r.status_code == 201, r.text
    client.post("/auth/logout")
    return email, r.json()["id"]


def test_erra_demais_e_leva_429_mesmo_com_a_senha_certa():
    with TestClient(app) as client:
        email, usuario_id = _conta(client)
        try:
            for i in range(auth.MAX_TENTATIVAS_LOGIN):
                r = client.post("/auth/login", json={"email": email, "senha": "errada12345"})
                assert r.status_code == 401, (i, r.text)

            # Passou do limite: nem a senha certa entra, que é o ponto — senão o
            # limite só atrasaria quem chuta, sem impedir.
            r = client.post("/auth/login", json={"email": email, "senha": "senha12345"})
            assert r.status_code == 429, r.text
            assert "tentativas" in r.json()["detail"].lower()
        finally:
            auth._TENTATIVAS_LOGIN.clear()
            with db.get_conn() as conn:
                conn.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))


def test_acertar_limpa_o_contador():
    with TestClient(app) as client:
        email, usuario_id = _conta(client)
        try:
            for _ in range(auth.MAX_TENTATIVAS_LOGIN - 1):
                assert client.post("/auth/login", json={"email": email, "senha": "errada12345"}).status_code == 401
            assert client.post("/auth/login", json={"email": email, "senha": "senha12345"}).status_code == 200
            # Zerado: dá para errar o limite inteiro de novo antes de bloquear.
            for _ in range(auth.MAX_TENTATIVAS_LOGIN):
                assert client.post("/auth/login", json={"email": email, "senha": "errada12345"}).status_code == 401
            assert client.post("/auth/login", json={"email": email, "senha": "senha12345"}).status_code == 429
        finally:
            auth._TENTATIVAS_LOGIN.clear()
            with db.get_conn() as conn:
                conn.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))


def test_conta_inexistente_tambem_conta_tentativa():
    """Se só as contas existentes fossem limitadas, o próprio limite viraria um
    oráculo de quem tem conta aqui."""
    with TestClient(app) as client:
        email = f"pytest_nada_{uuid.uuid4().hex[:10]}@teste.local"
        try:
            for _ in range(auth.MAX_TENTATIVAS_LOGIN):
                assert client.post("/auth/login", json={"email": email, "senha": "qualquer123"}).status_code == 401
            assert client.post("/auth/login", json={"email": email, "senha": "qualquer123"}).status_code == 429
        finally:
            auth._TENTATIVAS_LOGIN.clear()


def test_admin_sai_da_configuracao_e_nao_do_codigo(monkeypatch):
    """O e-mail do admin estava escrito no código, num repositório público.

    Sem o Streamlit no caminho sobra a variável de ambiente, que é como a API
    lê isto em produção; com ele, o `.streamlit/secrets.toml` tem precedência,
    igual ao `DATABASE_URL`.
    """
    monkeypatch.setitem(sys.modules, "streamlit", None)
    monkeypatch.delenv("ADMIN_EMAILS", raising=False)
    assert db.emails_admin() == set()          # sem configuração, ninguém é admin
    monkeypatch.setenv("ADMIN_EMAILS", " Alguem@Exemplo.com , outro@exemplo.com ")
    assert db.emails_admin() == {"alguem@exemplo.com", "outro@exemplo.com"}
