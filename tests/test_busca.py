"""
Busca global do topbar (MIGRACAO.md §5): ILIKE no enunciado das questões.
"""

import uuid

import db


def test_busca_global_encontra_questao(questao_teste):
    assert questao_teste in [q["id"] for q in db.busca_global("[pytest")]


def test_busca_global_ignora_maiusculas_minusculas(questao_teste):
    # Regressão: o LIKE do Postgres diferencia caixa (o do SQLite não); precisa ser ILIKE.
    assert questao_teste in [q["id"] for q in db.busca_global("[PYTEST")]


def test_busca_global_nao_encontra_termo_inexistente():
    assert db.busca_global(f"zzz_{uuid.uuid4().hex}_zzz") == []
