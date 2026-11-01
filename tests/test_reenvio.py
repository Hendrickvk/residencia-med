"""
Reenviar não pode gravar duas vezes, e falhar não pode perder: é o que o cliente
assume ao repetir uma resposta cujo retorno se perdeu (respostasQueue.ts e
respostasSimulado.ts). A rede em si é conferida no navegador; aqui fica o contrato.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

import db
import repeticao_espacada as sr
from api.main import app
from tests.conftest import confirmar_email


@pytest.fixture(autouse=True, scope="module")
def _tabelas_existem():
    db.init_db()


@pytest.fixture()
def conta_api():
    email = f"pytest_{uuid.uuid4().hex[:12]}@teste.local"
    with TestClient(app) as client:
        id_conta = client.post("/auth/signup", json={"email": email, "senha": "senha123"}).json()["id"]
        confirmar_email(id_conta)
        yield client, id_conta
    with db.get_conn() as conn:
        conn.execute("DELETE FROM usuarios WHERE email = ?", (email,))


def _contagens(usuario_id, questao_id):
    with db.get_conn() as conn:
        return conn.execute("""
            SELECT (SELECT COUNT(*) FROM respostas WHERE usuario_id = ? AND questao_id = ?) AS respostas,
                   (SELECT COUNT(*) FROM revisao_eventos WHERE usuario_id = ? AND questao_id = ?) AS eventos
        """, (usuario_id, questao_id, usuario_id, questao_id)).fetchone()


def test_resposta_reenviada_grava_uma_vez(conta_api, questao_teste):
    client, id_conta = conta_api
    corpo = {"questao_id": questao_teste, "alternativa": "A", "envio": uuid.uuid4().hex}
    primeira = client.post("/respostas", json=corpo)
    assert primeira.status_code == 200 and primeira.json()["ganho"]
    segunda = client.post("/respostas", json=corpo)
    assert segunda.status_code == 200 and segunda.json()["ganho"] is None
    linha = _contagens(id_conta, questao_teste)
    assert linha["respostas"] == 1 and linha["eventos"] == 1


def test_sem_envio_continua_gravando(conta_api, questao_teste):
    # Tela aberta do pacote antigo, durante a troca: não pode parar de gravar.
    client, id_conta = conta_api
    assert client.post("/respostas", json={"questao_id": questao_teste, "alternativa": "A"}).status_code == 200
    assert _contagens(id_conta, questao_teste)["respostas"] == 1


def test_envio_de_uma_conta_nao_vale_para_outra(usuario_teste, conta_api, questao_teste):
    client, id_conta = conta_api
    envio = uuid.uuid4().hex
    db.registrar_envio(usuario_teste, envio)
    client.post("/respostas", json={"questao_id": questao_teste, "alternativa": "A", "envio": envio})
    assert _contagens(id_conta, questao_teste)["respostas"] == 1


def test_avaliacao_reenviada_nao_empurra_o_sm2(conta_api, questao_teste):
    client, id_conta = conta_api
    client.post("/respostas", json={"questao_id": questao_teste, "alternativa": "A"})
    corpo = {"qualidade": 5, "alternativa": "A", "envio": uuid.uuid4().hex}
    assert client.post(f"/revisao/{questao_teste}/avaliar", json=corpo).status_code == 200
    estado = sr.estados_revisao([questao_teste], usuario_id=id_conta)[questao_teste]
    repetida = client.post(f"/revisao/{questao_teste}/avaliar", json=corpo)
    assert repetida.status_code == 200 and repetida.json()["repetido"] is True and repetida.json()["prazos"] is None
    assert sr.estados_revisao([questao_teste], usuario_id=id_conta)[questao_teste] == estado
    assert _contagens(id_conta, questao_teste)["eventos"] == 2


def test_nota_de_cartao_reenviada_grava_uma_vez(conta_api):
    client, id_conta = conta_api
    pasta = client.post("/cartoes/pastas", json={"nome": "t"}).json()["id"]
    baralho = client.post("/cartoes/baralhos", json={"nome": "t", "pasta_id": pasta}).json()["id"]
    cartao = client.post("/cartoes", json={"frente": "f", "verso": "v", "baralho_id": baralho}).json()["id"]
    corpo = {"qualidade": 4, "envio": uuid.uuid4().hex}
    assert client.post(f"/cartoes/{cartao}/avaliar", json=corpo).json()["ganho"]
    repetida = client.post(f"/cartoes/{cartao}/avaliar", json=corpo)
    assert repetida.status_code == 200 and repetida.json()["repetido"] is True
    with db.get_conn() as conn:
        eventos = conn.execute(
            "SELECT COUNT(*) AS n FROM revisao_cartao_eventos WHERE usuario_id = ? AND cartao_id = ?", (id_conta, cartao),
        ).fetchone()["n"]
    assert eventos == 1


def test_lista_de_marcadas_segue_sem_gabarito(conta_api, questao_teste):
    # O acesso novo pelo menu da conta leva à mesma lista: ela continua sem resposta.
    client, _ = conta_api
    client.post(f"/questoes/{questao_teste}/marcar")
    corpo = client.get("/me/marcadas").json()
    assert corpo["questoes"]
    for campo in ("resposta_correta", "explicacao", "alternativas"):
        assert campo not in corpo["questoes"][0]


def test_painel_diz_quantos_acertos_foram_no_chute(conta_api, questao_teste):
    client, _ = conta_api
    client.post("/respostas", json={"questao_id": questao_teste, "alternativa": "A", "confianca": "chute"})
    totais = client.get("/painel").json()["totais"]
    assert totais["respostas"] == 1 and float(totais["acertos"]) == 0.5 and totais["acertos_no_chute"] == 1


def test_projecao_diz_a_cobertura():
    temas = [
        {"subtopico_id": 1, "especialidade_id": 1, "area_id": 1, "questoes_provas": 30},
        {"subtopico_id": 2, "especialidade_id": 1, "area_id": 1, "questoes_provas": 70},
    ]
    tentativas = [{"area_id": 1, "especialidade_id": 1, "subtopico_id": 1, "pontos": 1}]
    assert db.projetar_nota(tentativas, temas)["cobertura"] == 30


def _prova(client, edicao):
    banca, nome, _ = edicao
    resposta = client.post("/simulados/oficial", json={"banca": banca, "edicao": nome})
    assert resposta.status_code == 201
    simulado_id = resposta.json()["id"]
    return simulado_id, [i["id"] for i in client.get(f"/simulados/{simulado_id}/itens").json()]


def test_resposta_depois_de_finalizar_nao_muda_a_prova(conta_api, edicao_teste):
    client, _ = conta_api
    simulado_id, ids = _prova(client, edicao_teste)
    assert client.post(f"/simulados/{simulado_id}/respostas", json={"questao_id": ids[0], "alternativa": "A"}).status_code == 200
    assert client.post(f"/simulados/{simulado_id}/finalizar").status_code == 200
    atrasada = client.post(f"/simulados/{simulado_id}/respostas", json={"questao_id": ids[0], "alternativa": "B"})
    assert atrasada.status_code == 409
    item = next(i for i in client.get(f"/simulados/{simulado_id}/itens").json() if i["id"] == ids[0])
    assert item["resposta_dada"] == "A"


def test_resposta_a_questao_inexistente_e_recusa_e_nao_erro(conta_api, edicao_teste):
    # Com 500, a fila do aparelho tentaria para sempre.
    client, _ = conta_api
    simulado_id, _ = _prova(client, edicao_teste)
    resposta = client.post(f"/simulados/{simulado_id}/respostas", json={"questao_id": 999999999, "alternativa": "A"})
    assert resposta.status_code == 403


def test_trocar_de_alternativa_vale_a_ultima(conta_api, edicao_teste):
    client, _ = conta_api
    simulado_id, ids = _prova(client, edicao_teste)
    for letra in ("A", "B", "B"):
        assert client.post(f"/simulados/{simulado_id}/respostas", json={"questao_id": ids[0], "alternativa": letra}).status_code == 200
    item = next(i for i in client.get(f"/simulados/{simulado_id}/itens").json() if i["id"] == ids[0])
    assert item["resposta_dada"] == "B"


def test_consolidacao_que_falhou_refaz_ao_tentar_de_novo(conta_api, edicao_teste, monkeypatch):
    client, id_conta = conta_api
    simulado_id, ids = _prova(client, edicao_teste)
    client.post(f"/simulados/{simulado_id}/respostas", json={"questao_id": ids[0], "alternativa": "A"})

    original = db.registrar_respostas_de_simulado

    def quebra(*args, **kwargs):
        raise RuntimeError("queda simulada")

    monkeypatch.setattr(db, "registrar_respostas_de_simulado", quebra)
    with TestClient(app, raise_server_exceptions=False, cookies=client.cookies) as outro:
        assert outro.post(f"/simulados/{simulado_id}/finalizar").status_code == 500
    assert _contagens(id_conta, ids[0])["respostas"] == 0
    assert client.get(f"/simulados/{simulado_id}").json()["finalizado_em"]  # Fechou, e falta consolidar.

    monkeypatch.setattr(db, "registrar_respostas_de_simulado", original)
    de_novo = client.post(f"/simulados/{simulado_id}/finalizar")
    assert de_novo.status_code == 200 and de_novo.json()["ganhos"]
    assert _contagens(id_conta, ids[0])["respostas"] == 1
    xp = client.get(f"/simulados/{simulado_id}").json()["xp_ganho"]
    assert xp > 0

    # Mais uma vez: não duplica nada e não zera o total da prova.
    terceira = client.post(f"/simulados/{simulado_id}/finalizar")
    assert terceira.status_code == 200 and terceira.json()["ganhos"] == []
    assert _contagens(id_conta, ids[0])["respostas"] == 1
    assert client.get(f"/simulados/{simulado_id}").json()["xp_ganho"] == xp


def test_limpar_envios_apaga_so_os_antigos(usuario_teste):
    novo, velho = uuid.uuid4().hex, uuid.uuid4().hex
    db.registrar_envio(usuario_teste, novo)
    db.registrar_envio(usuario_teste, velho)
    import datetime
    with db.get_conn() as conn:
        conn.execute(
            "UPDATE envios_processados SET criado_em = ? WHERE usuario_id = ? AND envio = ?",
            (db.agora_br() - datetime.timedelta(days=40), usuario_teste, velho),
        )
    db.limpar_envios(db.agora_br() - datetime.timedelta(days=30))
    assert db.envio_ja_registrado(usuario_teste, novo) and not db.envio_ja_registrado(usuario_teste, velho)
