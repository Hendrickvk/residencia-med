"""
Fixtures compartilhadas dos testes da API.

Os testes rodam num branch do Neon quando `DATABASE_URL_TESTES` existe (em
`.streamlit/secrets.toml` ou no ambiente); sem ela, no Neon de produção, como
sempre foi — e o começo da suíte avisa. Nos dois casos todo dado criado aqui é
marcado com um sufixo `uuid4` (e-mails `pytest_*@teste.local`, áreas
`__pytest_area_*`) e removido no teardown de cada fixture via `ON DELETE
CASCADE`. Nunca reaproveite dados de produção nem deixe uma fixture sem
teardown — e todo dado de teste precisa cair num desses dois padrões, que é o
que a varredura do início da suíte sabe apagar.
"""

import datetime
import json
import os
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Antes do `import db`: é o que faz o `db._database_url` preferir o branch de
# testes. O pool nasce na primeira conexão, então ainda dá tempo.
os.environ["CONDUTA_TESTES"] = "1"

import db  # noqa: E402

if not db._url_testes():
    print(
        "\n[conduta] ATENÇÃO: sem DATABASE_URL_TESTES, os testes rodam no banco de PRODUÇÃO. "
        "Crie um branch no Neon e ponha a connection string dele em .streamlit/secrets.toml "
        "como DATABASE_URL_TESTES.",
        file=sys.stderr,
    )


@pytest.fixture(scope="session", autouse=True)
def _apaga_sobras_de_rodadas_interrompidas():
    """Teardown só roda se o pytest chegar ao fim. Uma rodada morta no meio —
    Ctrl+C, ou o limite de tempo de quem chamou, e a suíte leva uns 7 minutos —
    deixa as fixtures em produção: foi assim que uma `__pytest_area_*` apareceu
    no filtro de Áreas do Praticar e quatro questões de teste ficaram no
    sorteio das sessões dos alunos (HISTORICO.md, 2026-09-24). Por isso a suíte
    começa apagando o que sobrou das anteriores; a área leva as questões dela
    por CASCADE, e a conta leva tudo que é dela.

    ponytail: supõe uma suíte por vez — duas rodadas simultâneas apagariam os
    dados uma da outra."""
    with db.get_conn() as conn:
        conn.execute(r"DELETE FROM areas WHERE nome LIKE '\_\_pytest\_area\_%'")
        conn.execute(r"DELETE FROM usuarios WHERE email LIKE 'pytest\_%@teste.local'")
    yield


@pytest.fixture(autouse=True)
def _zera_limitadores():
    """Os limitadores de login e de cadastro contam na memória do processo, e a
    suíte inteira chega ao servidor como um IP só: sem isto, o sexto `signup`
    de qualquer teste levaria 429 por causa dos cinco anteriores, de outros
    testes. Zera antes de cada um; quem testa o limitador conta do zero."""
    from api.routers import auth
    auth._TENTATIVAS_LOGIN.clear()
    yield


def confirmar_email(usuario_id):
    """Marca a conta como confirmada, sem passar pelo link.

    Desde 2026-09-23 conta nova nasce sem confirmar e o `/praticar/sessao` e a
    criação de simulado respondem 403 — então todo teste que cria conta pelo
    `/auth/signup` e vai buscar conteúdo precisa chamar isto. Quem testa a
    própria confirmação (`test_confirmacao_email.py`) usa o token de verdade.
    """
    with db.get_conn() as conn:
        conn.execute("UPDATE usuarios SET email_confirmado_em = ? WHERE id = ?", (db.agora_br(), usuario_id))


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


@pytest.fixture()
def quatro_questoes(area_teste):
    ids = []
    with db.get_conn() as conn:
        c = conn.cursor()
        for i in range(4):
            c.execute("""
                INSERT INTO questoes
                    (area_id, subtopico_id, enunciado, alternativas, resposta_correta,
                     explicacao, banca, ano, criada_em)
                VALUES (?, NULL, ?, ?, 'A', 'comentário de teste', 'PYTEST', 2024, ?)
            """, (
                area_teste,
                f"[pytest {uuid.uuid4().hex[:8]}] Questão {i} de teste automatizado — não é conteúdo real.",
                json.dumps({"A": "certa", "B": "errada"}, ensure_ascii=False),
                datetime.datetime.now().isoformat(),
            ))
            ids.append(c.lastrowid)
    yield ids
    with db.get_conn() as conn:
        for questao_id in ids:
            conn.execute("DELETE FROM questoes WHERE id = ?", (questao_id,))


@pytest.fixture()
def edicao_teste(area_teste):
    """Três questões de uma edição fictícia, inseridas fora da ordem do
    caderno. Devolve (banca, edicao, números inseridos)."""
    banca = "PYTEST"
    edicao = f"pytest-{uuid.uuid4().hex[:8]}"
    numeros = [30, 5, 12]
    ids = []
    with db.get_conn() as conn:
        c = conn.cursor()
        for numero in numeros:
            c.execute("""
                INSERT INTO questoes
                    (area_id, subtopico_id, enunciado, alternativas, resposta_correta,
                     explicacao, banca, ano, edicao, numero_prova, criada_em)
                VALUES (?, NULL, ?, ?, 'A', 'comentário de teste', ?, 2025, ?, ?, ?)
            """, (
                area_teste, f"[pytest {edicao}] Questão {numero} de teste automatizado — não é conteúdo real.",
                json.dumps({"A": "certa", "B": "errada"}, ensure_ascii=False),
                banca, edicao, numero, datetime.datetime.now().isoformat(),
            ))
            ids.append(c.lastrowid)
            c.execute(
                "INSERT INTO questoes_provas (questao_id, banca, edicao, numero_prova) VALUES (?, ?, ?, ?)",
                (ids[-1], banca, edicao, numero),
            )
    yield banca, edicao, numeros
    with db.get_conn() as conn:
        for questao_id in ids:
            conn.execute("DELETE FROM questoes WHERE id = ?", (questao_id,))
