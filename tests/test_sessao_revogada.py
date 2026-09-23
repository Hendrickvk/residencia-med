"""
Revogação de sessão (HISTORICO.md, item 4 do plano de endurecimento). O JWT é
stateless e vale 12 h: até esta mudança, `POST /auth/logout` só apagava o
cookie do navegador, e um token já copiado continuava entrando. O que estes
testes prendem é que ele para de entrar — pelo logout e pela redefinição de
senha, que é quando alguém desconfia de que a conta foi invadida.
"""

import hashlib
import uuid

from fastapi.testclient import TestClient

from api.main import app
from api.security import COOKIE_NOME

import db


def _conta(client, senha="senha123"):
    email = f"pytest_sessao_{uuid.uuid4().hex[:10]}@teste.local"
    r = client.post("/auth/signup", json={"email": email, "senha": senha})
    assert r.status_code == 201, r.text
    return email, r.json()["id"]


def test_logout_derruba_o_token_ja_copiado():
    with TestClient(app) as client:
        email, usuario_id = _conta(client)
        try:
            # O que um token roubado seria: o valor do cookie, guardado à parte.
            roubado = client.cookies[COOKIE_NOME]
            assert client.get("/me").status_code == 200

            client.post("/auth/logout")

            client.cookies.set(COOKIE_NOME, roubado)
            r = client.get("/me")
            assert r.status_code == 401, "token de antes do logout continuou valendo"
        finally:
            with db.get_conn() as conn:
                conn.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))


def test_redefinir_senha_derruba_as_sessoes_abertas():
    with TestClient(app) as client:
        email, usuario_id = _conta(client)
        try:
            antiga = client.cookies[COOKIE_NOME]

            token = "tok_" + uuid.uuid4().hex
            db.criar_token_senha(usuario_id, hashlib.sha256(token.encode()).hexdigest())
            r = client.post("/auth/senha/redefinir", json={"token": token, "senha": "novasenha456"})
            assert r.status_code == 200, r.text

            # A sessão que nasceu da própria redefinição continua valendo...
            assert client.get("/me").status_code == 200
            # ...e a de antes, não.
            client.cookies.set(COOKIE_NOME, antiga)
            assert client.get("/me").status_code == 401
        finally:
            with db.get_conn() as conn:
                conn.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))


def test_token_sem_versao_nao_entra():
    """Cookie emitido antes desta mudança: cai como inválido de propósito, em
    vez de passar sem conferência."""
    import datetime

    import jwt

    from api.security import JWT_ALGORITHM, JWT_SECRET

    with TestClient(app) as client:
        email, usuario_id = _conta(client)
        try:
            antigo = jwt.encode(
                {
                    "sub": str(usuario_id),
                    "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=12),
                },
                JWT_SECRET, algorithm=JWT_ALGORITHM,
            )
            client.cookies.set(COOKIE_NOME, antigo)
            assert client.get("/me").status_code == 401
        finally:
            with db.get_conn() as conn:
                conn.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
