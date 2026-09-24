"""
Flashcards da aluna: pasta > baralho > cartão, estudados pelo mesmo SM-2 das
questões.

Dois comportamentos são de segurança e não de conveniência: tudo é da conta
que pediu (mandar o id da pasta de outra pessoa não faz nada) e a cor da pasta
vem de uma lista fechada, porque vira CSS na tela.
"""

import uuid

from fastapi.testclient import TestClient

from api.main import app

import db


def _conta(client, prefixo="cart"):
    email = f"pytest_{prefixo}_{uuid.uuid4().hex[:10]}@teste.local"
    r = client.post("/auth/signup", json={"email": email, "senha": "senha123"})
    assert r.status_code == 201, r.text
    return email, r.json()["id"]


def _apagar(*emails):
    with db.get_conn() as conn:
        for email in emails:
            conn.execute("DELETE FROM usuarios WHERE email = ?", (email,))


def test_ciclo_completo_pasta_baralho_cartao_e_estudo():
    email = None
    try:
        with TestClient(app) as client:
            email, _ = _conta(client)

            pasta = client.post("/cartoes/pastas", json={"nome": "Ginecologia", "cor": "ameixa"}).json()["id"]
            baralho = client.post(
                "/cartoes/baralhos", json={"pasta_id": pasta, "nome": "Vulvovaginites"}
            ).json()["id"]
            cartao = client.post("/cartoes", json={
                "baralho_id": baralho,
                "frente": "Corrimento branco, grumoso, prurido intenso",
                "verso": "Candidíase vulvovaginal",
            }).json()["id"]

            # A árvore aparece inteira, com o que está vencido.
            pastas = client.get("/cartoes/pastas").json()["pastas"]
            assert len(pastas) == 1 and pastas[0]["cor"] == "ameixa"
            assert pastas[0]["baralhos"][0]["cartoes"] == 1
            # Cartão nunca visto conta como vencido, senão um baralho recém
            # escrito não teria o que estudar.
            assert pastas[0]["baralhos"][0]["vencidos"] == 1

            fila = client.get(f"/cartoes/baralhos/{baralho}/estudar").json()["cartoes"]
            assert [c["id"] for c in fila] == [cartao]
            # Os prazos de cada nota vêm junto, como na Revisão de casos.
            assert set(fila[0]["prazos"]) == {"1", "3", "4", "5"}

            # Acertar tira o cartão do dia.
            assert client.post(f"/cartoes/{cartao}/avaliar", json={"qualidade": 4}).status_code == 200
            assert client.get(f"/cartoes/baralhos/{baralho}/estudar").json()["cartoes"] == []
            assert client.get("/cartoes/pastas").json()["pastas"][0]["baralhos"][0]["vencidos"] == 0

            # Errar traz de volta ainda hoje (10 minutos, como nos casos).
            client.post(f"/cartoes/{cartao}/avaliar", json={"qualidade": 1})
            estado = db.estado_revisao_cartao(cartao, usuario_id=client.get("/me").json()["id"])
            assert estado["repeticoes"] == 0

            # Apagar a pasta leva baralho e cartão junto.
            assert client.delete(f"/cartoes/pastas/{pasta}").status_code == 204
            assert client.get("/cartoes/pastas").json()["pastas"] == []
            assert client.get(f"/cartoes/baralhos/{baralho}").status_code == 404
    finally:
        if email:
            _apagar(email)


def test_cartoes_de_outra_conta_nao_sao_alcancaveis():
    dona = alheia = None
    try:
        with TestClient(app) as client:
            dona, _ = _conta(client, "dona")
            pasta = client.post("/cartoes/pastas", json={"nome": "Minha", "cor": "rosa"}).json()["id"]
            baralho = client.post("/cartoes/baralhos", json={"pasta_id": pasta, "nome": "DSTs"}).json()["id"]
            cartao = client.post("/cartoes", json={
                "baralho_id": baralho, "frente": "f", "verso": "v",
            }).json()["id"]
            client.post("/auth/logout")

            alheia, _ = _conta(client, "alheia")
            # Com o id na mão, e ainda assim nada.
            assert client.get(f"/cartoes/baralhos/{baralho}").status_code == 404
            assert client.get(f"/cartoes/baralhos/{baralho}/estudar").status_code == 404
            assert client.post(f"/cartoes/{cartao}/avaliar", json={"qualidade": 5}).status_code == 404
            assert client.post("/cartoes/baralhos", json={"pasta_id": pasta, "nome": "invasão"}).status_code == 404
            assert client.post("/cartoes", json={
                "baralho_id": baralho, "frente": "x", "verso": "y",
            }).status_code == 400

            # Editar e apagar também não atravessam.
            client.patch(f"/cartoes/pastas/{pasta}", json={"nome": "roubada", "cor": "vinho"})
            client.delete(f"/cartoes/{cartao}")
            client.delete(f"/cartoes/pastas/{pasta}")
            assert client.get("/cartoes/pastas").json()["pastas"] == []

            client.post("/auth/logout")
            client.post("/auth/login", json={"email": dona, "senha": "senha123"})
            minhas = client.get("/cartoes/pastas").json()["pastas"]
            assert len(minhas) == 1, "a pasta da dona sumiu ou foi alterada por outra conta"
            assert minhas[0]["nome"] == "Minha"
            assert minhas[0]["baralhos"][0]["cartoes"] == 1
    finally:
        _apagar(*[e for e in (dona, alheia) if e])


def test_cor_fora_da_lista_cai_no_padrao():
    email = None
    try:
        with TestClient(app) as client:
            email, _ = _conta(client)
            # "verde" é da escala de triagem e não está na lista das pastas.
            client.post("/cartoes/pastas", json={"nome": "X", "cor": "verde"})
            assert client.get("/cartoes/pastas").json()["pastas"][0]["cor"] == db.COR_PASTA_PADRAO
    finally:
        if email:
            _apagar(email)


def test_cartao_guarda_de_qual_caso_nasceu(questao_teste):
    """Procedência: o cartão criado pela discussão do caso lembra de onde veio.
    Guardado desde já porque isso não se recupera depois — ninguém vai lembrar
    a origem de um cartão escrito há seis meses."""
    email = None
    try:
        with TestClient(app) as client:
            email, _ = _conta(client)
            pasta = client.post("/cartoes/pastas", json={"nome": "P", "cor": "indigo"}).json()["id"]
            baralho = client.post("/cartoes/baralhos", json={"pasta_id": pasta, "nome": "B"}).json()["id"]

            do_caso = client.post("/cartoes", json={
                "baralho_id": baralho, "frente": "f", "verso": "v", "questao_id": questao_teste,
            }).json()["id"]
            solto = client.post("/cartoes", json={
                "baralho_id": baralho, "frente": "f2", "verso": "v2",
            }).json()["id"]

            with db.get_conn() as conn:
                linhas = {
                    r["id"]: r["questao_id"]
                    for r in conn.execute(
                        "SELECT id, questao_id FROM cartoes WHERE id IN (?, ?)", (do_caso, solto)
                    ).fetchall()
                }
            assert linhas[do_caso] == questao_teste
            assert linhas[solto] is None
    finally:
        if email:
            _apagar(email)


def test_mover_baralho_de_pasta():
    email = None
    try:
        with TestClient(app) as client:
            email, _ = _conta(client)
            origem = client.post("/cartoes/pastas", json={"nome": "Origem", "cor": "ciano"}).json()["id"]
            destino = client.post("/cartoes/pastas", json={"nome": "Destino", "cor": "lavanda"}).json()["id"]
            baralho = client.post("/cartoes/baralhos", json={"pasta_id": origem, "nome": "B"}).json()["id"]

            client.patch(f"/cartoes/baralhos/{baralho}", json={"nome": "B renomeado", "pasta_id": destino})
            visto = client.get(f"/cartoes/baralhos/{baralho}").json()["baralho"]
            assert visto["nome"] == "B renomeado"
            assert visto["pasta"] == "Destino"

            # Pasta que não é dela não serve de destino: o baralho fica onde está.
            client.post("/auth/logout")
            outra_email = f"pytest_cart_{uuid.uuid4().hex[:10]}@teste.local"
            client.post("/auth/signup", json={"email": outra_email, "senha": "senha123"})
            alheia = client.post("/cartoes/pastas", json={"nome": "Alheia", "cor": "vinho"}).json()["id"]
            client.post("/auth/logout")
            client.post("/auth/login", json={"email": email, "senha": "senha123"})

            client.patch(f"/cartoes/baralhos/{baralho}", json={"nome": "B", "pasta_id": alheia})
            assert client.get(f"/cartoes/baralhos/{baralho}").json()["baralho"]["pasta"] == "Destino"
            _apagar(outra_email)
    finally:
        if email:
            _apagar(email)


def test_estudar_tudo_atravessa_os_baralhos():
    """Sem isto, oito baralhos vencidos custam oito sessões."""
    email = None
    try:
        with TestClient(app) as client:
            email, _ = _conta(client)
            pasta = client.post("/cartoes/pastas", json={"nome": "P", "cor": "ciano"}).json()["id"]
            a = client.post("/cartoes/baralhos", json={"pasta_id": pasta, "nome": "A"}).json()["id"]
            b = client.post("/cartoes/baralhos", json={"pasta_id": pasta, "nome": "B"}).json()["id"]
            for baralho in (a, b):
                for i in range(2):
                    client.post("/cartoes", json={"baralho_id": baralho, "frente": f"f{i}", "verso": "v"})

            fila = client.get("/cartoes/estudar").json()["cartoes"]
            assert len(fila) == 4
            # Cada cartão diz de qual baralho veio — é o que a tela mostra
            # quando a sessão atravessa baralhos.
            assert {c["baralho"] for c in fila} == {"A", "B"}
            assert all(c["cor"] == "ciano" for c in fila)

            # O baralho sozinho continua trazendo só os dele.
            assert len(client.get(f"/cartoes/baralhos/{a}/estudar").json()["cartoes"]) == 2
    finally:
        if email:
            _apagar(email)


def test_desfazer_devolve_o_cartao_ao_estado_anterior():
    """É para isto que o histórico existe desde o primeiro dia: o estado
    anterior está no evento anterior."""
    email = None
    try:
        with TestClient(app) as client:
            email, usuario_id = _conta(client)
            pasta = client.post("/cartoes/pastas", json={"nome": "P", "cor": "rosa"}).json()["id"]
            baralho = client.post("/cartoes/baralhos", json={"pasta_id": pasta, "nome": "B"}).json()["id"]
            cartao = client.post("/cartoes", json={
                "baralho_id": baralho, "frente": "f", "verso": "v",
            }).json()["id"]

            client.post(f"/cartoes/{cartao}/avaliar", json={"qualidade": 4})
            primeiro = dict(db.estado_revisao_cartao(cartao, usuario_id=usuario_id))
            client.post(f"/cartoes/{cartao}/avaliar", json={"qualidade": 5})
            assert dict(db.estado_revisao_cartao(cartao, usuario_id=usuario_id)) != primeiro

            assert client.post(f"/cartoes/{cartao}/desfazer").status_code == 200
            assert dict(db.estado_revisao_cartao(cartao, usuario_id=usuario_id)) == primeiro

            # Desfazendo a primeira, o cartão volta a ser novo.
            assert client.post(f"/cartoes/{cartao}/desfazer").status_code == 200
            assert db.estado_revisao_cartao(cartao, usuario_id=usuario_id) is None
            # E aí não há mais o que desfazer.
            assert client.post(f"/cartoes/{cartao}/desfazer").status_code == 404
    finally:
        if email:
            _apagar(email)
