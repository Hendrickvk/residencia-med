"""
Teto diário de casos do /praticar/sessao (HISTORICO.md, item 2 do plano de
endurecimento). O endpoint entrega gabarito e explicação embutidos por decisão
de arquitetura; o teto é o que impede que uma conta qualquer leve o banco
inteiro em seis requisições.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from api.main import app

import db
from tests.conftest import confirmar_email


@pytest.fixture(autouse=True, scope="module")
def _tabela_existe():
    """Os outros testes daqui sobem o TestClient, que chama `init_db` no
    lifespan; o primeiro é só de banco e precisaria da tabela já criada."""
    db.init_db()


def test_cota_libera_ate_o_teto_e_depois_nada(usuario_teste):
    assert db.consumir_cota_pratica(usuario_id=usuario_teste, quantidade=8, teto=10) == 8
    # Só sobram 2, mesmo pedindo 8: o saldo é por caso entregue.
    assert db.consumir_cota_pratica(usuario_id=usuario_teste, quantidade=8, teto=10) == 2
    assert db.consumir_cota_pratica(usuario_id=usuario_teste, quantidade=1, teto=10) == 0

    with db.get_conn() as conn:
        row = conn.execute(
            "SELECT entregues FROM cota_pratica WHERE usuario_id = ? AND dia = ?",
            (usuario_teste, db.hoje_br()),
        ).fetchone()
    assert row["entregues"] == 10


def test_sessao_devolve_429_com_a_cota_estourada(quatro_questoes, area_teste):
    email = f"pytest_cota_{uuid.uuid4().hex[:10]}@teste.local"
    usuario_id = None
    try:
        with TestClient(app) as client:
            usuario_id = client.post("/auth/signup", json={"email": email, "senha": "senha123"}).json()["id"]
            confirmar_email(usuario_id)

            r = client.get("/praticar/sessao", params={"area_id": area_teste, "quantidade": 2})
            assert r.status_code == 200
            assert len(r.json()["questoes"]) == 2

            # Gastou o que sobrava do dia: a próxima sessão não sai.
            db.consumir_cota_pratica(usuario_id=usuario_id, quantidade=db.TETO_DIARIO_PRATICA)
            r = client.get("/praticar/sessao", params={"area_id": area_teste, "quantidade": 2})
            assert r.status_code == 429
            assert str(db.TETO_DIARIO_PRATICA) in r.json()["detail"]
    finally:
        if usuario_id:
            with db.get_conn() as conn:
                conn.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))


def test_recorte_menor_que_o_pedido_gasta_so_o_que_entregou(quatro_questoes, area_teste):
    """Pedir 20 num recorte de 4 tem que cobrar 4 — senão um filtro estreito
    consome a cota do dia inteiro sem entregar nada."""
    email = f"pytest_cota_{uuid.uuid4().hex[:10]}@teste.local"
    usuario_id = None
    try:
        with TestClient(app) as client:
            usuario_id = client.post("/auth/signup", json={"email": email, "senha": "senha123"}).json()["id"]
            confirmar_email(usuario_id)
            r = client.get("/praticar/sessao", params={"area_id": area_teste, "quantidade": 20})
            assert r.status_code == 200
            assert len(r.json()["questoes"]) == 4

        with db.get_conn() as conn:
            row = conn.execute(
                "SELECT entregues FROM cota_pratica WHERE usuario_id = ? AND dia = ?",
                (usuario_id, db.hoje_br()),
            ).fetchone()
        assert row["entregues"] == 4
    finally:
        if usuario_id:
            with db.get_conn() as conn:
                conn.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
