"""
Fixtures compartilhadas dos testes da API.

Não existe banco de testes separado neste projeto (só o Neon de produção,
apontado por `.streamlit/secrets.toml`) — por isso todo dado criado aqui é
marcado com um sufixo `uuid4` (e-mails `pytest_*@teste.local`, áreas
`__pytest_area_*`) e removido no teardown de cada fixture via `ON DELETE
CASCADE`. Nunca reaproveite dados de produção nem deixe uma fixture sem
teardown.
"""

import datetime
import json
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import db  # noqa: E402


@pytest.fixture()
def usuario_teste():
    email = f"pytest_{uuid.uuid4().hex[:12]}@teste.local"
    usuario_id = db.criar_usuario(email, "hash-nao-usado-nestes-testes")
    yield usuario_id
    with db.get_conn() as conn:
        conn.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))


@pytest.fixture()
def area_teste():
    nome = f"__pytest_area_{uuid.uuid4().hex[:10]}"
    with db.get_conn() as conn:
        conn.execute("INSERT INTO areas (nome) VALUES (?)", (nome,))
        area_id = conn.execute("SELECT id FROM areas WHERE nome = ?", (nome,)).fetchone()["id"]
    yield area_id
    with db.get_conn() as conn:
        conn.execute("DELETE FROM areas WHERE id = ?", (area_id,))


@pytest.fixture()
def material_teste(area_teste):
    titulo = f"[pytest {uuid.uuid4().hex[:8]}] Material de teste automatizado"
    with db.get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO materiais (area_id, subtopico_id, tipo, titulo, link_mediafire)
            VALUES (?, NULL, 'Apostila', ?, 'https://www.mediafire.com/pytest')
        """, (area_teste, titulo))
        material_id = c.lastrowid
    yield material_id, titulo
    with db.get_conn() as conn:
        conn.execute("DELETE FROM materiais WHERE id = ?", (material_id,))


@pytest.fixture()
def questao_teste(area_teste):
    enunciado = f"[pytest {uuid.uuid4().hex[:8]}] Questão de teste automatizado — não é conteúdo real."
    with db.get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO questoes
                (area_id, subtopico_id, enunciado, alternativas, resposta_correta,
                 explicacao, banca, ano, criada_em)
            VALUES (?, NULL, ?, ?, 'A', 'comentário de teste', 'PYTEST', 2024, ?)
        """, (
            area_teste, enunciado, json.dumps({"A": "certa", "B": "errada"}, ensure_ascii=False),
            datetime.datetime.now().isoformat(),
        ))
        questao_id = c.lastrowid
    yield questao_id
    with db.get_conn() as conn:
        conn.execute("DELETE FROM questoes WHERE id = ?", (questao_id,))
