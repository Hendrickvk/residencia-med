"""
Confirmação de e-mail. O cadastro continua aberto a qualquer pessoa (decisão
de 2026-09-23): o que a confirmação faz é dar um custo a cada conta — uma
caixa de e-mail que funcione — sem transformar a plataforma em lista de
convidados. O que estes testes prendem é que o conteúdo só sai depois dela, e
que o token se comporta como o de senha (uso único, expira, queima os irmãos).
"""

import datetime
import hashlib
import uuid

import pytest
from fastapi.testclient import TestClient

from api.main import app

import db


def _hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@pytest.fixture()
def conta_nova():
    """Devolve `(client) -> (email, usuario_id)` e apaga a conta pelo
    **e-mail**, no teardown.

    Pelo e-mail, e não pelo id, porque o id só existe se o `/auth/signup`
    responder: quando ele criou a linha e quebrou logo depois (aconteceu aqui
    em 2026-09-23, com um `TypeError` no envio), o teste morria antes de
    guardar o id e a conta ficava para trás no banco de produção. O e-mail é
    sorteado antes da chamada, então o teardown sempre sabe o que apagar.
    """
    emails = []

    def _criar(client):
        email = f"pytest_conf_{uuid.uuid4().hex[:10]}@teste.local"
        emails.append(email)
        r = client.post("/auth/signup", json={"email": email, "senha": "senha123"})
        assert r.status_code == 201, r.text
        return email, r.json()["id"]

    yield _criar
    with db.get_conn() as conn:
        for email in emails:
            conn.execute("DELETE FROM usuarios WHERE email = ?", (email,))


def test_conta_nova_nasce_sem_confirmar_e_nao_recebe_questao(conta_nova, area_teste, quatro_questoes):
    with TestClient(app) as client:
        conta_nova(client)

        assert client.get("/me").json()["email_confirmado"] is False

        # A sessão existe (ela entra e vê o aviso), mas o conteúdo não sai.
        assert client.get("/praticar/sessao", params={"area_id": area_teste, "quantidade": 2}).status_code == 403
        assert client.post("/simulados", json={"num_questoes": 5, "tempo_limite_min": 10}).status_code == 403


def test_link_confirma_uma_vez_so_e_libera_o_conteudo(conta_nova, area_teste, quatro_questoes):
    with TestClient(app) as client:
        _, usuario_id = conta_nova(client)

        # O e-mail não sai para `@teste.local` (domínio reservado), então o
        # token vem do banco — é o mesmo que teria ido no link.
        token = "conf_" + uuid.uuid4().hex
        db.criar_token_confirmacao(usuario_id, _hash(token))

        assert client.post("/auth/confirmar", json={"token": token}).status_code == 200
        assert client.get("/me").json()["email_confirmado"] is True

        r = client.get("/praticar/sessao", params={"area_id": area_teste, "quantidade": 2})
        assert r.status_code == 200
        assert len(r.json()["questoes"]) == 2

        # Uso único: o mesmo link não serve de novo.
        assert client.post("/auth/confirmar", json={"token": token}).status_code == 400


def test_confirmar_queima_os_outros_links_pendentes(conta_nova):
    """Quem pediu reenvio fica com vários links válidos; usar um tem de
    invalidar os outros, como no fluxo de senha."""
    with TestClient(app) as client:
        _, usuario_id = conta_nova(client)
        primeiro, segundo = "conf_" + uuid.uuid4().hex, "conf_" + uuid.uuid4().hex
        db.criar_token_confirmacao(usuario_id, _hash(primeiro))
        db.criar_token_confirmacao(usuario_id, _hash(segundo))

        assert client.post("/auth/confirmar", json={"token": segundo}).status_code == 200
        assert client.post("/auth/confirmar", json={"token": primeiro}).status_code == 400


def test_token_vencido_e_token_inexistente_respondem_igual(conta_nova):
    with TestClient(app) as client:
        _, usuario_id = conta_nova(client)
        vencido = "conf_" + uuid.uuid4().hex
        db.criar_token_confirmacao(usuario_id, _hash(vencido), horas_validade=-1)

        r_vencido = client.post("/auth/confirmar", json={"token": vencido})
        r_inexistente = client.post("/auth/confirmar", json={"token": "nao_existe_" + uuid.uuid4().hex})
        assert r_vencido.status_code == r_inexistente.status_code == 400
        assert r_vencido.json() == r_inexistente.json()


def test_reenvio_tem_limite_e_conta_confirmada_nao_gasta_link(conta_nova):
    with TestClient(app) as client:
        _, usuario_id = conta_nova(client)
        # O signup já criou um link; o limite é por janela, contando todos.
        for _ in range(2):
            assert client.post("/auth/confirmar/reenviar").status_code == 200
        assert client.post("/auth/confirmar/reenviar").status_code == 429

        with db.get_conn() as conn:
            conn.execute(
                "UPDATE usuarios SET email_confirmado_em = ? WHERE id = ?",
                (datetime.datetime.now(), usuario_id),
            )
        # Confirmada: responde ok sem criar link nenhum, mesmo estourado o limite.
        assert client.post("/auth/confirmar/reenviar").status_code == 200


def test_conta_criada_direto_no_banco_nasce_sem_confirmar(usuario_teste):
    """`criar_usuario` não confirma nada por conta própria: quem confirma é o
    link. (As contas anteriores à migração entraram confirmadas por um UPDATE
    único no `init_db`, conferido à mão — testar isso aqui dependeria dos dados
    de produção.)"""
    assert db.obter_usuario(usuario_teste)["email_confirmado_em"] is None
