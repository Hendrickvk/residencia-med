"""
Rotina diária (scripts/rotina_diaria.py, 26/09): o lembrete de revisão por
e-mail — opcional, desligado por padrão —, as questões suspeitas e o relatório
do dia para o admin.
"""

import datetime
import uuid

from fastapi.testclient import TestClient

import db
from api.email_modelo import lembrete_revisao
from api.main import app
from tests.conftest import confirmar_email


def test_lembrete_nasce_desligado_e_so_vai_para_quem_ligou(usuario_teste):
    hoje = db.hoje_br()

    def candidatas(dia=hoje):
        return [c["id"] for c in db.contas_para_lembrete(dia)]

    assert usuario_teste not in candidatas()  # nasce desligado
    db.definir_lembrete_revisao(usuario_teste, True)
    assert usuario_teste not in candidatas()  # e-mail ainda não confirmado
    confirmar_email(usuario_teste)
    assert usuario_teste in candidatas()
    db.marcar_lembrete_enviado(usuario_teste, hoje)
    assert usuario_teste not in candidatas()  # um por dia
    assert usuario_teste in candidatas(hoje + datetime.timedelta(days=1))


def test_perfil_liga_e_desliga_o_lembrete():
    # E-mail sorteado antes da chamada, para o `finally` achar a conta (CLAUDE.md).
    email = f"pytest_lembrete_{uuid.uuid4().hex[:10]}@teste.local"
    try:
        with TestClient(app) as client:
            assert client.post("/auth/signup", json={"email": email, "senha": "senha123"}).status_code == 201
            assert client.get("/me").json()["lembrete_revisao"] is False
            assert client.patch("/me/lembrete", json={"ativo": True}).status_code == 200
            assert client.get("/me").json()["lembrete_revisao"] is True
            assert client.patch("/me/lembrete", json={"ativo": False}).status_code == 200
            assert client.get("/me").json()["lembrete_revisao"] is False
    finally:
        with db.get_conn() as conn:
            conn.execute("DELETE FROM usuarios WHERE email = ?", (email,))


def test_texto_do_lembrete():
    assunto, texto, html = lembrete_revisao(casos=12, cartoes=1, segundos_por_caso=75, app_url="https://x")
    assert assunto == "12 casos e 1 cartão para revisar hoje"
    assert "uns 15 minutos" in texto and "https://x/revisao" in texto
    # Todo lembrete leva o caminho para desligar, nas duas versões.
    assert "https://x/perfil#lembretes" in texto and 'href="https://x/perfil#lembretes"' in html
    # Só cartão: o botão vai direto para o estudo dos baralhos.
    assunto, texto, _ = lembrete_revisao(casos=0, cartoes=3, segundos_por_caso=75, app_url="https://x")
    assert assunto == "3 cartões para revisar hoje" and "https://x/baralhos?estudar=tudo" in texto


def test_relatorio_do_dia_so_sai_uma_vez():
    tipo = f"pytest_{uuid.uuid4().hex[:8]}"
    try:
        assert db.reservar_envio_diario(tipo, db.hoje_br()) is True
        assert db.reservar_envio_diario(tipo, db.hoje_br()) is False
    finally:
        with db.get_conn() as conn:
            conn.execute("DELETE FROM envios_diarios WHERE tipo = ?", (tipo,))


def test_resumo_do_dia_conta_quem_estudou(usuario_teste, questao_teste):
    db.registrar_resposta(questao_teste, "A", True, usuario_id=usuario_teste)
    resumo = db.resumo_do_dia(db.hoje_br(), excluir_testes=False)
    assert resumo["estudaram"] >= 1 and resumo["respostas"] >= 1


def test_questao_que_a_maioria_erra_na_mesma_alternativa_fica_suspeita(questao_teste):
    # A questão de teste tem gabarito A; cinco contas marcam B.
    contas = [db.criar_usuario(f"pytest_{uuid.uuid4().hex[:12]}@teste.local", "hash-nao-usado") for _ in range(5)]
    try:
        for conta in contas:
            db.registrar_resposta(questao_teste, "B", False, usuario_id=conta)
        suspeitas = db.questoes_suspeitas(excluir_testes=False, limite=10_000)
        alvo = next(s for s in suspeitas if s["id"] == questao_teste)
        assert alvo["errada_mais_marcada"] == "B"
        assert alvo["maioria_errada"] == 1.0 and alvo["acerto"] == 0
        # Com as contas de teste de fora (o padrão), ela some.
        assert all(s["id"] != questao_teste for s in db.questoes_suspeitas(limite=10_000))
    finally:
        with db.get_conn() as conn:
            for conta in contas:
                conn.execute("DELETE FROM usuarios WHERE id = ?", (conta,))
