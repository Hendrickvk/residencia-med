"""
A loja e a proteção de ofensiva (progressao.py): moeda que some ou aparece, item
comprado duas vezes e ofensiva quebrada por engano são o que este arquivo impede.
"""

import datetime
import threading
import uuid

import pytest
from fastapi.testclient import TestClient

import db
import progressao
import repeticao_espacada as sr
from api.main import app
from api.routers.me import obter_me
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


def _dar(usuario_id, *, moedas=0, xp=0):
    """Saldo direto na conta de teste, pelo razão, para o saldo seguir igual à soma."""
    agora = db.agora_br()
    with db.get_conn() as conn:
        progressao._lancar(
            conn, usuario_id=usuario_id, chave=f"teste:{uuid.uuid4().hex}", tipo="teste", xp=xp, moedas=moedas,
            area_id=None, agora=agora,
        )


def _saldo(usuario_id):
    with db.get_conn() as conn:
        return conn.execute("SELECT xp_total, moedas FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()


def _soma_razao(usuario_id):
    with db.get_conn() as conn:
        return conn.execute(
            "SELECT COALESCE(SUM(xp), 0) AS xp, COALESCE(SUM(moedas), 0) AS moedas FROM progresso_eventos WHERE usuario_id = ?",
            (usuario_id,),
        ).fetchone()


def _item(loja, item_id):
    return next(i for s in loja["secoes"] for i in s["itens"] if i["id"] == item_id)


NIVEL_10 = progressao.xp_do_nivel(10)


# --- Comprar ----------------------------------------------------------------

def test_compra_desconta_e_o_item_passa_a_ser_dela(usuario_teste):
    _dar(usuario_teste, moedas=500, xp=NIVEL_10)
    loja = progressao.comprar("milimetrado", usuario_id=usuario_teste)
    assert loja["moedas"] == 250
    assert _item(loja, "milimetrado")["seu"] is True
    saldo, razao = _saldo(usuario_teste), _soma_razao(usuario_teste)
    assert saldo["moedas"] == razao["moedas"] == 250


def test_comprar_duas_vezes_nao_cobra_de_novo(usuario_teste):
    _dar(usuario_teste, moedas=1000, xp=NIVEL_10)
    progressao.comprar("milimetrado", usuario_id=usuario_teste)
    with pytest.raises(progressao.CompraRecusada):
        progressao.comprar("milimetrado", usuario_id=usuario_teste)
    assert _saldo(usuario_teste)["moedas"] == 750


def test_nivel_insuficiente_recusa(usuario_teste):
    _dar(usuario_teste, moedas=5000, xp=NIVEL_10)
    with pytest.raises(progressao.CompraRecusada, match="Nível 15"):
        progressao.comprar("plantao", usuario_id=usuario_teste)
    assert _saldo(usuario_teste)["moedas"] == 5000


def test_saldo_insuficiente_recusa_e_nao_deixa_o_item(usuario_teste):
    _dar(usuario_teste, moedas=249, xp=NIVEL_10)
    with pytest.raises(progressao.CompraRecusada, match="moedas"):
        progressao.comprar("milimetrado", usuario_id=usuario_teste)
    assert _saldo(usuario_teste)["moedas"] == 249
    assert _item(progressao.loja(usuario_teste), "milimetrado")["seu"] is False


def test_duas_compras_ao_mesmo_tempo_com_saldo_para_uma(usuario_teste):
    """O caso que uma leitura seguida de escrita deixaria passar: as duas leem 300 e
    as duas compram. O saldo nunca pode ficar negativo, nem o item sair de graça."""
    _dar(usuario_teste, moedas=300, xp=NIVEL_10)
    resultados = []
    barreira = threading.Barrier(2)

    def tentar(item):
        barreira.wait()
        try:
            progressao.comprar(item, usuario_id=usuario_teste)
            resultados.append(item)
        except progressao.CompraRecusada:
            pass

    fios = [threading.Thread(target=tentar, args=(i,)) for i in ("milimetrado", "pontos")]
    for f in fios:
        f.start()
    for f in fios:
        f.join()

    assert len(resultados) == 1
    preco = progressao.ITENS[resultados[0]]["preco"]
    assert _saldo(usuario_teste)["moedas"] == 300 - preco
    assert _soma_razao(usuario_teste)["moedas"] == 300 - preco


def test_titulo_de_area_pede_o_nivel_da_area(usuario_teste, area_teste):
    _dar(usuario_teste, moedas=1000, xp=NIVEL_10)
    with pytest.raises(progressao.CompraRecusada, match="Nível 5 em Cirurgia"):
        progressao.comprar("mao-de-cirurgiao", usuario_id=usuario_teste)
    with db.get_conn() as conn:
        cirurgia = conn.execute("SELECT id FROM areas WHERE nome = 'Cirurgia'").fetchone()["id"]
        progressao._lancar(
            conn, usuario_id=usuario_teste, chave="teste:area", tipo="teste", xp=1000, moedas=0,
            area_id=cirurgia, agora=db.agora_br(),
        )
    assert _item(progressao.comprar("mao-de-cirurgiao", usuario_id=usuario_teste), "mao-de-cirurgiao")["seu"] is True


def test_moldura_de_patente_nao_se_compra(usuario_teste):
    _dar(usuario_teste, moedas=1000, xp=NIVEL_10)
    with pytest.raises(progressao.CompraRecusada):
        progressao.comprar("sutura", usuario_id=usuario_teste)


def test_item_inexistente(usuario_teste):
    with pytest.raises(progressao.ItemInexistente):
        progressao.comprar("nao-existe", usuario_id=usuario_teste)


# --- Equipar ----------------------------------------------------------------

def test_sem_escolha_a_moldura_e_a_da_patente(usuario_teste):
    _dar(usuario_teste, xp=NIVEL_10)
    assert progressao.equipados_de(db.obter_usuario(usuario_teste))["moldura"] == "sutura"
    assert _item(progressao.loja(usuario_teste), "sutura")["em_uso"] is True


def test_ciclo_basico_nao_tem_moldura(usuario_teste):
    assert progressao.equipados_de(db.obter_usuario(usuario_teste)) == {"moldura": None, "titulo": None}


def test_equipar_o_que_e_dela(usuario_teste):
    _dar(usuario_teste, moedas=1000, xp=NIVEL_10)
    progressao.comprar("milimetrado", usuario_id=usuario_teste)
    progressao.comprar("plantonista", usuario_id=usuario_teste)
    progressao.equipar("moldura", "milimetrado", usuario_id=usuario_teste)
    progressao.equipar("titulo", "plantonista", usuario_id=usuario_teste)
    assert progressao.equipados_de(db.obter_usuario(usuario_teste)) == {
        "moldura": "milimetrado", "titulo": "Plantonista",
    }


def test_equipar_item_que_nao_e_dela_recusa(usuario_teste):
    _dar(usuario_teste, moedas=1000, xp=NIVEL_10)
    with pytest.raises(progressao.CompraRecusada):
        progressao.equipar("moldura", "milimetrado", usuario_id=usuario_teste)
    # A moldura de uma patente que ela ainda não alcançou também não é dela.
    with pytest.raises(progressao.CompraRecusada):
        progressao.equipar("moldura", "residencia", usuario_id=usuario_teste)
    # Título no encaixe da moldura não existe.
    with pytest.raises(progressao.ItemInexistente):
        progressao.equipar("moldura", "plantonista", usuario_id=usuario_teste)


def test_tirar_a_moldura_fica_gravado_mesmo_trocando_de_patente(usuario_teste):
    _dar(usuario_teste, xp=NIVEL_10)
    progressao.equipar("moldura", None, usuario_id=usuario_teste)
    assert progressao.equipados_de(db.obter_usuario(usuario_teste))["moldura"] is None
    _dar(usuario_teste, xp=progressao.xp_do_nivel(20) - NIVEL_10)
    assert progressao.equipados_de(db.obter_usuario(usuario_teste))["moldura"] is None


# --- Consumíveis ------------------------------------------------------------

def test_a_primeira_protecao_e_de_graca_e_a_guarda_vai_ate_duas(usuario_teste):
    assert db.obter_usuario(usuario_teste)["protecoes_ofensiva"] == 1
    _dar(usuario_teste, moedas=500)
    loja = progressao.comprar(progressao.PROTECAO_OFENSIVA, usuario_id=usuario_teste)
    assert loja["protecao"]["tem"] == 2
    assert loja["moedas"] == 500 - progressao.PRECO_PROTECAO
    with pytest.raises(progressao.CompraRecusada):
        progressao.comprar(progressao.PROTECAO_OFENSIVA, usuario_id=usuario_teste)
    assert _saldo(usuario_teste)["moedas"] == 500 - progressao.PRECO_PROTECAO


def test_protecao_sem_saldo_nao_entra_na_guarda(usuario_teste):
    with pytest.raises(progressao.CompraRecusada):
        progressao.comprar(progressao.PROTECAO_OFENSIVA, usuario_id=usuario_teste)
    assert db.obter_usuario(usuario_teste)["protecoes_ofensiva"] == 1


def test_xp_em_dobro_vale_por_30_minutos_e_nao_empilha(usuario_teste, quatro_questoes):
    _dar(usuario_teste, moedas=500)
    assert progressao.prever_casos(quatro_questoes[:1], usuario_id=usuario_teste)[quatro_questoes[0]]["certo"] == 10
    loja = progressao.comprar(progressao.XP_EM_DOBRO, usuario_id=usuario_teste)
    assert loja["xp_dobro"]["ate"] is not None
    with pytest.raises(progressao.CompraRecusada):
        progressao.comprar(progressao.XP_EM_DOBRO, usuario_id=usuario_teste)

    # A tela promete o dobro, e o razão paga o dobro. A moeda não dobra por isso.
    previsao = progressao.prever_casos(quatro_questoes[:1], usuario_id=usuario_teste)[quatro_questoes[0]]
    assert previsao == {"certo": 20, "errado": 10}
    ganho = sr.registrar_revisao(
        quatro_questoes[0], 5, usuario_id=usuario_teste, origem="pratica", correta=True, alternativa="A",
    )["ganho"]
    assert (ganho["xp"], ganho["moedas"]) == (20, 2)

    with db.get_conn() as conn:
        conn.execute(
            "UPDATE usuarios SET xp_dobro_ate = ? WHERE id = ?",
            (db.agora_br() - datetime.timedelta(minutes=1), usuario_teste),
        )
    assert sr.registrar_revisao(
        quatro_questoes[1], 5, usuario_id=usuario_teste, origem="pratica", correta=True, alternativa="A",
    )["ganho"]["xp"] == 10


# --- Proteção de ofensiva ---------------------------------------------------

def _estudou(usuario_id, questao_id, dias_atras):
    """Uma resposta, escrita direto na data pedida: a ofensiva lê `respostas`."""
    dia = db.hoje_br() - datetime.timedelta(days=dias_atras)
    with db.get_conn() as conn:
        conn.execute("""
            INSERT INTO respostas (usuario_id, questao_id, resposta_dada, correta, respondida_em)
            VALUES (?, ?, 'A', 1, ?)
        """, (usuario_id, questao_id, dia.isoformat()))


def _me(usuario_id):
    return obter_me(usuario=db.obter_usuario(usuario_id))


def test_regra_do_buraco():
    hoje = datetime.date(2026, 10, 31)
    d = lambda n: hoje - datetime.timedelta(days=n)  # noqa: E731
    regra = progressao.dias_a_proteger
    # Estudou ontem: não há buraco.
    assert regra({d(1)}, set(), hoje, 2) == []
    # Um dia sem estudo, com uma proteção.
    assert regra({d(2)}, set(), hoje, 1) == [d(1)]
    # Dois dias sem estudo, com uma só: não gasta para perder do mesmo jeito.
    assert regra({d(3)}, set(), hoje, 1) == []
    assert regra({d(3)}, set(), hoje, 2) == [d(2), d(1)]
    # Nunca estudou: não há ofensiva a salvar.
    assert regra(set(), set(), hoje, 2) == []
    # O dia já protegido conta como parte da ofensiva.
    assert regra({d(3)}, {d(2)}, hoje, 1) == [d(1)]


def test_protecao_segura_a_ofensiva_e_o_dia_protegido_nao_conta(usuario_teste, questao_teste):
    _estudou(usuario_teste, questao_teste, 3)
    _estudou(usuario_teste, questao_teste, 2)
    me = _me(usuario_teste)
    # Dois dias de estudo, ontem protegido: a ofensiva é 2, e não 3 nem 0.
    assert me.ofensiva_dias == 2
    assert me.ofensiva_protegida_ontem is True
    assert db.obter_usuario(usuario_teste)["protecoes_ofensiva"] == 0


def test_me_de_novo_nao_gasta_outra_protecao(usuario_teste, questao_teste):
    with db.get_conn() as conn:
        conn.execute("UPDATE usuarios SET protecoes_ofensiva = 2 WHERE id = ?", (usuario_teste,))
    _estudou(usuario_teste, questao_teste, 2)
    _me(usuario_teste)
    _me(usuario_teste)
    assert db.obter_usuario(usuario_teste)["protecoes_ofensiva"] == 1


def test_buraco_maior_que_a_guarda_nao_gasta_e_a_ofensiva_cai(usuario_teste, questao_teste):
    _estudou(usuario_teste, questao_teste, 3)
    me = _me(usuario_teste)
    assert me.ofensiva_dias == 0
    assert me.ofensiva_protegida_ontem is False
    assert db.obter_usuario(usuario_teste)["protecoes_ofensiva"] == 1


def test_quem_estudou_ontem_nao_gasta_protecao(usuario_teste, questao_teste):
    _estudou(usuario_teste, questao_teste, 1)
    assert _me(usuario_teste).ofensiva_dias == 1
    assert db.obter_usuario(usuario_teste)["protecoes_ofensiva"] == 1


# --- O que a tela promete, e a API ------------------------------------------

def test_proximo_desbloqueio_diz_o_que_vem():
    libera = progressao.proximo_desbloqueio(14)
    assert libera["nivel"] == 15
    assert "a moldura Plantão" in libera["frase"]
    assert "o título Noite de plantão" in libera["frase"]
    assert progressao.proximo_desbloqueio(999) is None


def test_ids_do_catalogo_sao_unicos_e_o_catalogo_nao_vende_ajuda():
    ids = [i["id"] for i in progressao.CATALOGO]
    assert len(ids) == len(set(ids))
    assert {i["tipo"] for i in progressao.CATALOGO} <= {"moldura", "titulo", "tema", "estampa", "efeito"}


def test_api_da_loja(conta_api):
    client, id_conta = conta_api
    loja = client.get("/progresso/loja").json()
    assert loja["moedas"] == 0
    assert _item(loja, "pontos")["liberado"] is False

    _dar(id_conta, moedas=300, xp=progressao.xp_do_nivel(5))
    r = client.post("/progresso/loja/pontos/comprar")
    assert r.status_code == 200
    assert r.json()["moedas"] == 100

    assert client.post("/progresso/loja/pontos/comprar").status_code == 409
    assert client.post("/progresso/loja/nao-existe/comprar").status_code == 404
    assert client.put("/progresso/equipar", json={"tipo": "moldura", "item": "plantao"}).status_code == 409

    assert client.put("/progresso/equipar", json={"tipo": "moldura", "item": "pontos"}).status_code == 200
    me = client.get("/me").json()
    assert me["equipados"]["moldura"] == "pontos"
    assert me["moedas"] == 100
    assert me["progresso"]["libera"]["nivel"] > 5


def test_loja_exige_sessao():
    with TestClient(app) as client:
        assert client.get("/progresso/loja").status_code == 401
        assert client.post("/progresso/loja/pontos/comprar").status_code == 401


def test_retroagir_nao_apaga_as_compras(usuario_teste, questao_teste):
    """O script refaz o saldo pela soma do razão: compra tem de seguir descontada."""
    import importlib.util
    from pathlib import Path

    spec = importlib.util.spec_from_file_location(
        "retroagir_progresso", Path(__file__).resolve().parent.parent / "scripts" / "retroagir_progresso.py",
    )
    retroagir = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(retroagir)

    _dar(usuario_teste, moedas=500, xp=NIVEL_10)
    progressao.comprar("milimetrado", usuario_id=usuario_teste)
    sr.registrar_revisao(questao_teste, 5, usuario_id=usuario_teste, origem="pratica", correta=True, alternativa="A")
    antes = _saldo(usuario_teste)
    with db.get_conn() as conn:
        areas = {q["id"]: q["area_id"] for q in conn.execute("SELECT id, area_id FROM questoes").fetchall()}
        linha = conn.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_teste,)).fetchone()
        retroagir.retroagir_conta(conn, linha, areas)
    assert _saldo(usuario_teste) == antes
