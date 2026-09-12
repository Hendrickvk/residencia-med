"""
Testes da Fase 5 do MIGRACAO.md: gabarito não pode vazar num simulado em
andamento, e o estado "marcada" (dívida do HANDOFF_REDESIGN.md) precisa
estar disponível pra sustentar o terceiro estado da grade de navegação.

Chama as funções dos routers diretamente (sem TestClient/HTTP) passando
`usuario=` explícito — os fixtures de usuário não têm senha em texto plano
pra fazer login de verdade via `/auth/login`, e aqui o que importa é a
lógica do endpoint, não a autenticação (já coberta em test_api_smoke.py).
"""

import db
from api.routers.simulados import disponiveis as disponiveis_endpoint
from api.routers.simulados import finalizar as finalizar_endpoint
from api.routers.simulados import itens as itens_endpoint


def _usuario(usuario_id):
    return {"id": usuario_id, "email": "pytest@teste.local"}


def test_itens_simulado_nao_vaza_gabarito_antes_de_finalizar(usuario_teste, questao_teste):
    simulado_id = db.criar_simulado(None, None, 1, 10, [questao_teste], usuario_id=usuario_teste)

    payload_antes = itens_endpoint(simulado_id, usuario=_usuario(usuario_teste))
    assert payload_antes[0]["id"] == questao_teste
    assert "resposta_correta" not in payload_antes[0]
    assert "explicacao" not in payload_antes[0]

    finalizar_endpoint(simulado_id, usuario=_usuario(usuario_teste))

    payload_depois = itens_endpoint(simulado_id, usuario=_usuario(usuario_teste))
    assert payload_depois[0]["resposta_correta"] == "A"


def test_listar_itens_simulado_inclui_estado_marcada(usuario_teste, questao_teste):
    simulado_id = db.criar_simulado(None, None, 1, 10, [questao_teste], usuario_id=usuario_teste)

    itens = db.listar_itens_simulado(simulado_id, usuario_id=usuario_teste)
    assert itens[0]["marcada"] is False

    db.marcar_questao(usuario_teste, questao_teste)
    itens = db.listar_itens_simulado(simulado_id, usuario_id=usuario_teste)
    assert itens[0]["marcada"] is True


def test_disponiveis_conta_questoes_sem_filtro(usuario_teste):
    resultado = disponiveis_endpoint(area_id=None, banca=None, usuario=_usuario(usuario_teste))
    assert resultado["total"] >= 1
