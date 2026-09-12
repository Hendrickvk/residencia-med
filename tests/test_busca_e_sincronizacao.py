"""
Fase 6 do MIGRACAO.md: busca global precisa buscar de verdade (LIKE em
enunciado de questão e título de material, agrupado por tipo) — e o status
de sincronização do MediaFire é informativo, visível a qualquer aluno
logado, não só admin.
"""

import uuid

import db
from api.routers.sincronizacao import status_sincronizacao


def _usuario(usuario_id):
    return {"id": usuario_id, "email": "pytest@teste.local"}


def test_busca_global_encontra_questao_e_material(usuario_teste, questao_teste, material_teste):
    material_id, titulo_material = material_teste

    # O trecho comum "[pytest " está tanto no enunciado da questão quanto
    # no título do material, então uma busca por ele encontra os dois.
    resultado = db.busca_global("[pytest")
    ids_questoes = [q["id"] for q in resultado["questoes"]]
    ids_materiais = [m["id"] for m in resultado["materiais"]]
    assert questao_teste in ids_questoes
    assert material_id in ids_materiais

    material_encontrado = next(m for m in resultado["materiais"] if m["id"] == material_id)
    assert material_encontrado["link_mediafire"] == "https://www.mediafire.com/pytest"


def test_busca_global_ignora_maiusculas_minusculas(material_teste):
    material_id, titulo_material = material_teste
    # O título é gerado com "[pytest " (minúsculo) — busca em CAIXA ALTA
    # tem que encontrar do mesmo jeito (regressão: Postgres LIKE é
    # case-sensitive por padrão, diferente do SQLite; usar ILIKE).
    resultado = db.busca_global("[PYTEST")
    assert material_id in [m["id"] for m in resultado["materiais"]]


def test_listar_materiais_paginado_busca_ignora_caixa(material_teste):
    material_id, titulo_material = material_teste
    termo_maiusculo = titulo_material.upper()
    resultados = db.listar_materiais_paginado(busca=termo_maiusculo)
    assert material_id in [m["id"] for m in resultados]


def test_busca_global_nao_encontra_termo_inexistente():
    termo_improvavel = f"zzz_{uuid.uuid4().hex}_zzz"
    resultado = db.busca_global(termo_improvavel)
    assert resultado["questoes"] == []
    assert resultado["materiais"] == []


def test_status_sincronizacao_nao_exige_admin(usuario_teste):
    # usuario_teste não está em ADMIN_EMAILS — se essa chamada exigisse
    # admin, levantaria HTTPException 403 aqui.
    resultado = status_sincronizacao(usuario=_usuario(usuario_teste))
    assert "ultima_sincronizacao" in resultado
