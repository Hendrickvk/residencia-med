"""
A página de perfil expõe duas coisas que existiam no banco e não tinham porta:
a lista de questões marcadas e a data da prova.

O que este teste prende é o contorno da lista: ela mostra o suficiente para
reconhecer a questão e **não** o gabarito. Se um dia alguém "completar" esse
retorno com as alternativas, marcar as 1074 questões (os ids são sequenciais)
e pedir a lista uma vez levaria o banco inteiro, contornando o teto diário.
"""

import uuid

from fastapi.testclient import TestClient

from api.main import app

import db
from tests.conftest import confirmar_email


def test_marcadas_listam_sem_gabarito_e_praticar_so_as_marcadas(area_teste, quatro_questoes):
    email = f"pytest_pag_{uuid.uuid4().hex[:10]}@teste.local"
    try:
        with TestClient(app) as client:
            usuario_id = client.post("/auth/signup", json={"email": email, "senha": "senha123"}).json()["id"]
            confirmar_email(usuario_id)

            assert client.get("/me/marcadas").json()["questoes"] == []

            marcada, outra = quatro_questoes[0], quatro_questoes[1]
            assert client.post(f"/questoes/{marcada}/marcar").status_code in (200, 201)

            lista = client.get("/me/marcadas").json()["questoes"]
            assert [q["id"] for q in lista] == [marcada]
            item = lista[0]
            assert item["enunciado"] and item["area"]
            for proibido in ("alternativas", "resposta_correta", "explicacao", "imagem"):
                assert proibido not in item, f"a lista de marcadas não pode devolver {proibido}"

            # O filtro leva só as marcadas — e é por ele que o conteúdo sai.
            sessao = client.get("/praticar/sessao", params={"apenas_marcadas": True, "quantidade": 20})
            assert [q["id"] for q in sessao.json()["questoes"]] == [marcada]

            # Desmarcar tira da lista.
            assert client.delete(f"/questoes/{marcada}/marcar").status_code in (200, 204)
            assert client.get("/me/marcadas").json()["questoes"] == []
            assert outra  # só para deixar claro que as outras nunca entraram
    finally:
        with db.get_conn() as conn:
            conn.execute("DELETE FROM usuarios WHERE email = ?", (email,))


def test_data_da_prova_grava_e_limpa():
    email = f"pytest_pag_{uuid.uuid4().hex[:10]}@teste.local"
    try:
        with TestClient(app) as client:
            assert client.post("/auth/signup", json={"email": email, "senha": "senha123"}).status_code == 201
            assert client.get("/me").json()["prova_alvo"] is None

            assert client.patch("/me/prova", json={"data": "2026-12-24"}).status_code == 200
            assert client.get("/me").json()["prova_alvo"] == "2026-12-24"

            # Data malformada não entra: a contagem regressiva calcula em cima disto.
            assert client.patch("/me/prova", json={"data": "24/12/2026"}).status_code == 422
            assert client.get("/me").json()["prova_alvo"] == "2026-12-24"

            assert client.patch("/me/prova", json={"data": None}).status_code == 200
            assert client.get("/me").json()["prova_alvo"] is None
    finally:
        with db.get_conn() as conn:
            conn.execute("DELETE FROM usuarios WHERE email = ?", (email,))
