"""
Redefinição de senha: o que este teste prende é o comportamento de segurança,
não o caminho felizinho. Sem chave de e-mail no ambiente de teste, o envio
falha de propósito — e os endpoints têm que se comportar igual, porque a
resposta ao usuário não pode depender de o e-mail ter saído.
"""

import datetime
import hashlib
import uuid

from fastapi.testclient import TestClient

from api.main import app

import db


def _hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _criar_conta(client, senha="senha123"):
    email = f"pytest_senha_{uuid.uuid4().hex[:10]}@teste.local"
    r = client.post("/auth/signup", json={"email": email, "senha": senha})
    assert r.status_code == 201, r.text
    client.post("/auth/logout")
    return email, r.json()["id"]


def test_esqueci_responde_igual_para_conta_que_existe_e_que_nao_existe():
    with TestClient(app) as client:
        email, usuario_id = _criar_conta(client)
        try:
            existe = client.post("/auth/senha/esqueci", json={"email": email})
            nao_existe = client.post("/auth/senha/esqueci", json={"email": "ninguem_aqui@teste.local"})
            # Mesmo status e mesmo corpo: é o que impede descobrir quem tem conta.
            assert existe.status_code == nao_existe.status_code == 200
            assert existe.json() == nao_existe.json() == {"ok": True}
        finally:
            with db.get_conn() as conn:
                conn.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))


def test_token_troca_a_senha_uma_vez_e_derruba_os_outros_pendentes():
    with TestClient(app) as client:
        email, usuario_id = _criar_conta(client)
        try:
            # Dois pedidos: o segundo link é o que ela vai usar, e usar um
            # link tem de invalidar o outro.
            primeiro, segundo = "tok_" + uuid.uuid4().hex, "tok_" + uuid.uuid4().hex
            db.criar_token_senha(usuario_id, _hash(primeiro))
            db.criar_token_senha(usuario_id, _hash(segundo))

            r = client.post("/auth/senha/redefinir", json={"token": segundo, "senha": "novasenha456"})
            assert r.status_code == 200, r.text
            assert r.json()["email"] == email

            # Entra com a senha nova e não com a antiga.
            client.post("/auth/logout")
            assert client.post("/auth/login", json={"email": email, "senha": "senha123"}).status_code == 401
            assert client.post("/auth/login", json={"email": email, "senha": "novasenha456"}).status_code == 200

            # Reuso do mesmo link e uso do link irmão: os dois já morreram.
            for token in (segundo, primeiro):
                r = client.post("/auth/senha/redefinir", json={"token": token, "senha": "outra123456"})
                assert r.status_code == 400, token
        finally:
            with db.get_conn() as conn:
                conn.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))


def test_token_expirado_e_token_inventado_falham_igual():
    with TestClient(app) as client:
        email, usuario_id = _criar_conta(client)
        try:
            vencido = "tok_" + uuid.uuid4().hex
            db.criar_token_senha(usuario_id, _hash(vencido), minutos_validade=-1)

            expirado = client.post("/auth/senha/redefinir", json={"token": vencido, "senha": "novasenha456"})
            inventado = client.post(
                "/auth/senha/redefinir", json={"token": "tok_" + uuid.uuid4().hex, "senha": "novasenha456"}
            )
            assert expirado.status_code == inventado.status_code == 400
            assert expirado.json()["detail"] == inventado.json()["detail"]
            # A senha antiga continua valendo.
            assert client.post("/auth/login", json={"email": email, "senha": "senha123"}).status_code == 200
        finally:
            with db.get_conn() as conn:
                conn.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))


def test_limite_de_pedidos_por_conta():
    with TestClient(app) as client:
        email, usuario_id = _criar_conta(client)
        try:
            for _ in range(5):
                assert client.post("/auth/senha/esqueci", json={"email": email}).status_code == 200
            # Passou de 3 na janela: os pedidos seguintes não geram token novo.
            assert db.contar_tokens_recentes(usuario_id) == 3
        finally:
            with db.get_conn() as conn:
                conn.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))


def test_token_fica_no_banco_apenas_como_hash():
    with TestClient(app) as client:
        email, usuario_id = _criar_conta(client)
        try:
            client.post("/auth/senha/esqueci", json={"email": email})
            with db.get_conn() as conn:
                linha = conn.execute(
                    "SELECT token_hash, expira_em FROM senha_tokens WHERE usuario_id = ?", (usuario_id,)
                ).fetchone()
            assert linha is not None
            # 64 hexadecimais: é SHA-256, não o token que foi para o e-mail.
            assert len(linha["token_hash"]) == 64 and int(linha["token_hash"], 16) >= 0
            assert linha["expira_em"] > datetime.datetime.now()
        finally:
            with db.get_conn() as conn:
                conn.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))


def test_nao_tenta_entregar_em_dominio_reservado():
    """A suíte cria contas `@teste.local`, que não existem no DNS. Com a chave
    do Brevo no ambiente, tentar entregar nelas geraria bounce — e bounce em
    conta gratuita queima a reputação do remetente."""
    from api.email import destinatario_real

    assert destinatario_real("alguem@gmail.com")
    for reservado in ("x@teste.local", "x@algo.test", "x@a.invalid", "x@a.example", "x@qa.localhost"):
        assert not destinatario_real(reservado), reservado
