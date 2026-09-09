"""
Camada de acesso ao banco de dados (Postgres) da plataforma de preparação
para residência médica.

Todas as tabelas e funções de CRUD/consulta usadas pelo app Streamlit
ficam centralizadas aqui, para manter a interface (app.py) enxuta.
"""

import os
import json
import datetime
from contextlib import contextmanager

import psycopg2
import psycopg2.errors
import psycopg2.extensions
from psycopg2.extras import RealDictCursor

# Postgres retorna colunas NUMERIC/DECIMAL (ex: resultado de ROUND()) como
# Decimal por padrão no psycopg2 — o SQLite sempre devolvia float aqui.
# Isso quebra silenciosamente gráficos do Streamlit (Altair não reconhece
# Decimal como tipo numérico, e desenha eixo categórico em vez de
# quantitativo). Registrar esse conversor global faz NUMERIC/DECIMAL virar
# float sempre, restaurando o comportamento que o resto do código já espera.
_DEC2FLOAT = psycopg2.extensions.new_type(
    psycopg2.extensions.DECIMAL.values, "DEC2FLOAT",
    lambda value, curs: float(value) if value is not None else None,
)
psycopg2.extensions.register_type(_DEC2FLOAT)


def _database_url():
    """Lê a connection string do Postgres. Prioriza st.secrets (rodando
    via `streamlit run`); cai para a variável de ambiente DATABASE_URL
    quando não há contexto Streamlit (ex: scripts standalone). Nunca
    hardcoded no repo."""
    try:
        import streamlit as st
        if "DATABASE_URL" in st.secrets:
            return st.secrets["DATABASE_URL"]
    except Exception:
        pass
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL não configurada. Defina em .streamlit/secrets.toml "
            "(rodando via `streamlit run`) ou na variável de ambiente "
            "DATABASE_URL (para scripts standalone)."
        )
    return url


class _PGCursor:
    """Envolve um cursor real do psycopg2 pra imitar a API do
    sqlite3.Cursor usada neste arquivo: .execute() encadeável (retorna
    self, permitindo `conn.execute(...).fetchall()`), .fetchall()/
    .fetchone(), .rowcount, e .lastrowid.

    Postgres não tem `lastrowid` nativo — é calculado rodando
    `SELECT LASTVAL()` (último valor de sequence gerado nesta sessão)
    logo após um INSERT simples (sem ON CONFLICT ... DO NOTHING, que
    ainda consome um valor de sequence mesmo quando a linha é
    descartada — nenhum dos usos reais de .lastrowid neste arquivo
    segue esse padrão)."""

    def __init__(self, raw_cursor, raw_conn):
        self._cursor = raw_cursor
        self._conn = raw_conn
        self._was_insert = False
        self._lastrowid_fetched = False
        self._lastrowid_cache = None

    def execute(self, query, params=()):
        query = query.replace("?", "%s")
        # params=None faz o psycopg2 executar a query como está, sem tentar
        # interpretar '%' como marcador de substituição — necessário pra
        # queries sem parâmetros que tenham um '%' literal no texto (ex:
        # scripts administrativos com LIKE 'algo%' embutido na query).
        self._cursor.execute(query, params or None)
        self._was_insert = query.strip().upper().startswith("INSERT")
        self._lastrowid_fetched = False
        return self

    def fetchall(self):
        return self._cursor.fetchall()

    def fetchone(self):
        return self._cursor.fetchone()

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def lastrowid(self):
        if not self._was_insert:
            return None
        if not self._lastrowid_fetched:
            self._lastrowid_fetched = True
            with self._conn.cursor() as tmp:
                tmp.execute("SELECT LASTVAL()")
                self._lastrowid_cache = tmp.fetchone()[0]
        return self._lastrowid_cache


class _PGConnection:
    """Envolve uma conexão real do psycopg2 pra imitar a API do
    sqlite3.Connection usada neste arquivo: tanto `conn.execute(...)`
    direto quanto `c = conn.cursor(); c.execute(...)` funcionam, e as
    linhas retornadas são dict-like (`row["coluna"]`), igual
    sqlite3.Row."""

    def __init__(self, raw_conn):
        self._conn = raw_conn

    def execute(self, query, params=()):
        return self.cursor().execute(query, params)

    def cursor(self):
        return _PGCursor(self._conn.cursor(cursor_factory=RealDictCursor), self._conn)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


@contextmanager
def get_conn():
    # Importante: código que precisa capturar uma exceção de SQL e
    # continuar (ex: criar_usuario, para tratar e-mail duplicado) tem
    # que deixar a exceção propagar para FORA deste `with` inteiro — se
    # for capturada por dentro do `with`, a função segue normalmente e o
    # conn.commit() abaixo roda em cima de uma transação já abortada
    # pelo Postgres (InFailedSqlTransaction).
    raw_conn = psycopg2.connect(_database_url())
    conn = _PGConnection(raw_conn)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Cria as tabelas caso ainda não existam e popula áreas padrão."""
    with get_conn() as conn:
        c = conn.cursor()

        c.execute("""
        CREATE TABLE IF NOT EXISTS areas (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL UNIQUE
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS subtopicos (
            id SERIAL PRIMARY KEY,
            area_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            FOREIGN KEY (area_id) REFERENCES areas(id) ON DELETE CASCADE,
            UNIQUE(area_id, nome)
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS questoes (
            id SERIAL PRIMARY KEY,
            area_id INTEGER NOT NULL,
            subtopico_id INTEGER,
            enunciado TEXT NOT NULL,
            alternativas TEXT NOT NULL,   -- JSON: {"A": "...", "B": "...", ...}
            resposta_correta TEXT NOT NULL,  -- ex: "A"
            explicacao TEXT,
            banca TEXT,                  -- ex: ENAMED, USP-SP, UNIFESP, SCMSP...
            ano INTEGER,
            criada_em TEXT NOT NULL,
            FOREIGN KEY (area_id) REFERENCES areas(id) ON DELETE CASCADE,
            FOREIGN KEY (subtopico_id) REFERENCES subtopicos(id) ON DELETE SET NULL
        )
        """)

        # Usuários da plataforma (autenticação por e-mail/senha). Precisa
        # existir antes de respostas/revisao/simulados, que referenciam
        # usuarios(id) — o Postgres valida FK na hora do DDL.
        c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
            criado_em TEXT NOT NULL
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS respostas (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER NOT NULL,
            questao_id INTEGER NOT NULL,
            resposta_dada TEXT NOT NULL,
            correta INTEGER NOT NULL,   -- 0 ou 1
            respondida_em TEXT NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
            FOREIGN KEY (questao_id) REFERENCES questoes(id) ON DELETE CASCADE
        )
        """)

        # Repetição espaçada (SM-2 simplificado) — estado é por usuário
        # por questão, por isso a chave primária composta.
        c.execute("""
        CREATE TABLE IF NOT EXISTS revisao (
            usuario_id INTEGER NOT NULL,
            questao_id INTEGER NOT NULL,
            facilidade REAL NOT NULL DEFAULT 2.5,
            intervalo_dias INTEGER NOT NULL DEFAULT 1,
            repeticoes INTEGER NOT NULL DEFAULT 0,
            proxima_revisao TEXT NOT NULL,
            PRIMARY KEY (usuario_id, questao_id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
            FOREIGN KEY (questao_id) REFERENCES questoes(id) ON DELETE CASCADE
        )
        """)

        # Materiais (MediaFire) — biblioteca compartilhada entre todos os usuários
        c.execute("""
        CREATE TABLE IF NOT EXISTS materiais (
            id SERIAL PRIMARY KEY,
            area_id INTEGER NOT NULL,
            subtopico_id INTEGER,
            tipo TEXT NOT NULL,     -- Apostila / Videoaula / Video Bonus / Video Apostila / Outro
            titulo TEXT NOT NULL,
            link_mediafire TEXT NOT NULL,
            mediafire_key TEXT,     -- quickkey do arquivo no MediaFire (usado p/ evitar duplicar na sincronização)
            sincronizado_em TEXT,
            FOREIGN KEY (area_id) REFERENCES areas(id) ON DELETE CASCADE,
            FOREIGN KEY (subtopico_id) REFERENCES subtopicos(id) ON DELETE SET NULL
        )
        """)

        # Migração leve: adiciona colunas novas em bancos já existentes
        c.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'materiais'
        """)
        colunas_existentes = {row["column_name"] for row in c.fetchall()}
        if "mediafire_key" not in colunas_existentes:
            c.execute("ALTER TABLE materiais ADD COLUMN mediafire_key TEXT")
        if "sincronizado_em" not in colunas_existentes:
            c.execute("ALTER TABLE materiais ADD COLUMN sincronizado_em TEXT")
        if "arquivo_local" not in colunas_existentes:
            # caminho relativo (a partir da raiz do projeto) do arquivo baixado
            # para cache local; NULL enquanto só existir o link do MediaFire
            c.execute("ALTER TABLE materiais ADD COLUMN arquivo_local TEXT")
        if "tamanho_bytes" not in colunas_existentes:
            c.execute("ALTER TABLE materiais ADD COLUMN tamanho_bytes INTEGER")
        if "cache_atualizado_em" not in colunas_existentes:
            c.execute("ALTER TABLE materiais ADD COLUMN cache_atualizado_em TEXT")

        # Evita reimportar o mesmo arquivo do MediaFire duas vezes
        c.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_materiais_mfkey
            ON materiais(mediafire_key) WHERE mediafire_key IS NOT NULL
        """)

        # Simulados cronometrados — cada simulado pertence a um usuário
        c.execute("""
        CREATE TABLE IF NOT EXISTS simulados (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER NOT NULL,
            area_id INTEGER,              -- filtro usado (NULL = todas as áreas)
            banca TEXT,                   -- filtro usado (NULL/'' = todas as bancas)
            num_questoes INTEGER NOT NULL,
            tempo_limite_min INTEGER NOT NULL,
            iniciado_em TEXT NOT NULL,
            finalizado_em TEXT,           -- NULL enquanto em andamento
            acertos INTEGER,
            total_respondidas INTEGER,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
            FOREIGN KEY (area_id) REFERENCES areas(id) ON DELETE SET NULL
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS simulado_itens (
            id SERIAL PRIMARY KEY,
            simulado_id INTEGER NOT NULL,
            questao_id INTEGER NOT NULL,
            ordem INTEGER NOT NULL,
            resposta_dada TEXT,           -- NULL até responder
            correta INTEGER,              -- 0/1, calculada ao salvar resposta; NULL = não respondida
            FOREIGN KEY (simulado_id) REFERENCES simulados(id) ON DELETE CASCADE,
            FOREIGN KEY (questao_id) REFERENCES questoes(id) ON DELETE CASCADE,
            UNIQUE(simulado_id, ordem)
        )
        """)

        conn.commit()

        # Seed de áreas padrão (comuns em provas de residência / ENAMED)
        areas_padrao = [
            "Clínica Médica", "Cirurgia Geral", "Pediatria",
            "Ginecologia e Obstetrícia", "Medicina Preventiva e Social",
            "Cardiologia", "Dermatologia", "Ortopedia", "Neurologia",
            "Psiquiatria", "Endocrinologia", "Nefrologia", "Urologia",
        ]
        for nome in areas_padrao:
            c.execute("INSERT INTO areas (nome) VALUES (?) ON CONFLICT (nome) DO NOTHING", (nome,))
        conn.commit()


# ---------------------------------------------------------------------------
# Áreas e subtópicos
# ---------------------------------------------------------------------------

def listar_areas():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM areas ORDER BY nome").fetchall()


def criar_area(nome):
    with get_conn() as conn:
        conn.execute("INSERT INTO areas (nome) VALUES (?) ON CONFLICT (nome) DO NOTHING", (nome,))


def obter_ou_criar_area(nome):
    """Retorna o id da área, criando-a se ainda não existir. Usado pelos
    importadores em massa (planilha e MediaFire)."""
    nome = nome.strip()
    with get_conn() as conn:
        conn.execute("INSERT INTO areas (nome) VALUES (?) ON CONFLICT (nome) DO NOTHING", (nome,))
        row = conn.execute("SELECT id FROM areas WHERE nome = ?", (nome,)).fetchone()
        return row["id"]


def listar_subtopicos(area_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM subtopicos WHERE area_id = ? ORDER BY nome", (area_id,)
        ).fetchall()


def criar_subtopico(area_id, nome):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO subtopicos (area_id, nome) VALUES (?, ?) ON CONFLICT (area_id, nome) DO NOTHING",
            (area_id, nome),
        )


def obter_ou_criar_subtopico(area_id, nome):
    """Retorna o id do subtópico dentro da área, criando-o se necessário."""
    nome = nome.strip()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO subtopicos (area_id, nome) VALUES (?, ?) ON CONFLICT (area_id, nome) DO NOTHING",
            (area_id, nome),
        )
        row = conn.execute(
            "SELECT id FROM subtopicos WHERE area_id = ? AND nome = ?", (area_id, nome)
        ).fetchone()
        return row["id"]


# ---------------------------------------------------------------------------
# Questões
# ---------------------------------------------------------------------------

def criar_questao(area_id, subtopico_id, enunciado, alternativas: dict,
                   resposta_correta, explicacao="", banca="", ano=None):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO questoes
                (area_id, subtopico_id, enunciado, alternativas, resposta_correta,
                 explicacao, banca, ano, criada_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            area_id, subtopico_id, enunciado, json.dumps(alternativas, ensure_ascii=False),
            resposta_correta, explicacao, banca, ano,
            datetime.datetime.now().isoformat(),
        ))


def listar_questoes(area_id=None, subtopico_id=None):
    """Mantido para compatibilidade (usado na fila de 'Responder Questões',
    que só guarda os ids, então carregar tudo é barato). Para telas que
    RENDERIZAM cada questão na página, use listar_questoes_paginado."""
    query = "SELECT * FROM questoes WHERE 1=1"
    params = []
    if area_id:
        query += " AND area_id = ?"
        params.append(area_id)
    if subtopico_id:
        query += " AND subtopico_id = ?"
        params.append(subtopico_id)
    query += " ORDER BY criada_em DESC"
    with get_conn() as conn:
        return conn.execute(query, params).fetchall()


def _clausulas_filtro_questoes(area_id, subtopico_id, busca):
    condicoes = ["1=1"]
    params = []
    if area_id:
        condicoes.append("area_id = ?")
        params.append(area_id)
    if subtopico_id:
        condicoes.append("subtopico_id = ?")
        params.append(subtopico_id)
    if busca:
        condicoes.append("enunciado LIKE ?")
        params.append(f"%{busca}%")
    return " AND ".join(condicoes), params


def listar_questoes_paginado(area_id=None, subtopico_id=None, busca=None, limite=50, offset=0):
    condicao, params = _clausulas_filtro_questoes(area_id, subtopico_id, busca)
    query = f"SELECT * FROM questoes WHERE {condicao} ORDER BY criada_em DESC LIMIT ? OFFSET ?"
    with get_conn() as conn:
        return conn.execute(query, params + [limite, offset]).fetchall()


def contar_questoes_filtradas(area_id=None, subtopico_id=None, busca=None):
    condicao, params = _clausulas_filtro_questoes(area_id, subtopico_id, busca)
    query = f"SELECT COUNT(*) AS n FROM questoes WHERE {condicao}"
    with get_conn() as conn:
        return conn.execute(query, params).fetchone()["n"]


def questao_ja_existe(area_id, enunciado):
    """Checagem simples de duplicidade usada na importação em massa
    (mesma área + mesmo enunciado exato)."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM questoes WHERE area_id = ? AND enunciado = ?",
            (area_id, enunciado),
        ).fetchone()
        return row is not None


def contar_questoes():
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) AS n FROM questoes").fetchone()["n"]


def obter_questao(questao_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM questoes WHERE id = ?", (questao_id,)
        ).fetchone()


def excluir_questao(questao_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM questoes WHERE id = ?", (questao_id,))


# ---------------------------------------------------------------------------
# Respostas / desempenho
# ---------------------------------------------------------------------------

def registrar_resposta(questao_id, resposta_dada, correta: bool, *, usuario_id):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO respostas (usuario_id, questao_id, resposta_dada, correta, respondida_em)
            VALUES (?, ?, ?, ?, ?)
        """, (usuario_id, questao_id, resposta_dada, int(correta), datetime.datetime.now().isoformat()))


def desempenho_por_area(*, usuario_id):
    """Retorna total de respostas, acertos e % de acerto por área."""
    with get_conn() as conn:
        return conn.execute("""
            SELECT a.nome AS area,
                   COUNT(r.id) AS total,
                   SUM(r.correta) AS acertos,
                   ROUND(100.0 * SUM(r.correta) / COUNT(r.id), 1) AS pct_acerto
            FROM respostas r
            JOIN questoes q ON q.id = r.questao_id
            JOIN areas a ON a.id = q.area_id
            WHERE r.usuario_id = ?
            GROUP BY a.nome
            ORDER BY pct_acerto ASC
        """, (usuario_id,)).fetchall()


def desempenho_por_subtopico(area_id=None, *, usuario_id):
    query = """
        SELECT a.nome AS area, s.nome AS subtopico,
               COUNT(r.id) AS total,
               SUM(r.correta) AS acertos,
               ROUND(100.0 * SUM(r.correta) / COUNT(r.id), 1) AS pct_acerto
        FROM respostas r
        JOIN questoes q ON q.id = r.questao_id
        JOIN areas a ON a.id = q.area_id
        LEFT JOIN subtopicos s ON s.id = q.subtopico_id
        WHERE r.usuario_id = ?
    """
    params = [usuario_id]
    if area_id:
        query += " AND q.area_id = ?"
        params.append(area_id)
    query += " GROUP BY a.nome, s.nome ORDER BY pct_acerto ASC"
    with get_conn() as conn:
        return conn.execute(query, params).fetchall()


def evolucao_diaria(*, usuario_id):
    """Total de respostas e % de acerto por dia (para gráfico de evolução)."""
    with get_conn() as conn:
        return conn.execute("""
            SELECT substr(respondida_em, 1, 10) AS dia,
                   COUNT(*) AS total,
                   SUM(correta) AS acertos,
                   ROUND(100.0 * SUM(correta) / COUNT(*), 1) AS pct_acerto
            FROM respostas
            WHERE usuario_id = ?
            GROUP BY dia
            ORDER BY dia ASC
        """, (usuario_id,)).fetchall()


def desempenho_por_banca(*, usuario_id):
    """Retorna total de respostas, acertos e % de acerto por banca/
    instituição (ex: ENAMED, USP-SP, UNIFESP). Questões sem banca
    definida não entram — use `contar_respostas_sem_banca` para saber
    quantas ficaram de fora."""
    with get_conn() as conn:
        return conn.execute("""
            SELECT q.banca AS banca,
                   COUNT(r.id) AS total,
                   SUM(r.correta) AS acertos,
                   ROUND(100.0 * SUM(r.correta) / COUNT(r.id), 1) AS pct_acerto
            FROM respostas r
            JOIN questoes q ON q.id = r.questao_id
            WHERE q.banca IS NOT NULL AND TRIM(q.banca) != '' AND r.usuario_id = ?
            GROUP BY q.banca
            ORDER BY pct_acerto ASC
        """, (usuario_id,)).fetchall()


def desempenho_por_banca_e_area(*, usuario_id):
    """Cruza banca x área (para uma tabela pivô comparando o desempenho
    em cada área, banca a banca). Mesma exclusão de banca em branco de
    `desempenho_por_banca`."""
    with get_conn() as conn:
        return conn.execute("""
            SELECT q.banca AS banca, a.nome AS area,
                   COUNT(r.id) AS total,
                   SUM(r.correta) AS acertos,
                   ROUND(100.0 * SUM(r.correta) / COUNT(r.id), 1) AS pct_acerto
            FROM respostas r
            JOIN questoes q ON q.id = r.questao_id
            JOIN areas a ON a.id = q.area_id
            WHERE q.banca IS NOT NULL AND TRIM(q.banca) != '' AND r.usuario_id = ?
            GROUP BY q.banca, a.nome
            ORDER BY q.banca, a.nome
        """, (usuario_id,)).fetchall()


def contar_respostas_sem_banca(*, usuario_id):
    with get_conn() as conn:
        return conn.execute("""
            SELECT COUNT(*) AS n
            FROM respostas r
            JOIN questoes q ON q.id = r.questao_id
            WHERE (q.banca IS NULL OR TRIM(q.banca) = '') AND r.usuario_id = ?
        """, (usuario_id,)).fetchone()["n"]


def questoes_mais_erradas(limite=15, *, usuario_id):
    with get_conn() as conn:
        return conn.execute("""
            SELECT q.id, q.enunciado, a.nome AS area,
                   COUNT(r.id) AS total_respostas,
                   SUM(CASE WHEN r.correta = 0 THEN 1 ELSE 0 END) AS erros,
                   ROUND(100.0 * SUM(CASE WHEN r.correta = 0 THEN 1 ELSE 0 END) / COUNT(r.id), 1) AS pct_erro
            FROM respostas r
            JOIN questoes q ON q.id = r.questao_id
            JOIN areas a ON a.id = q.area_id
            WHERE r.usuario_id = ?
            GROUP BY q.id, a.nome
            HAVING COUNT(r.id) >= 1
            ORDER BY pct_erro DESC, total_respostas DESC
            LIMIT ?
        """, (usuario_id, limite)).fetchall()


# ---------------------------------------------------------------------------
# Importação em massa
# ---------------------------------------------------------------------------

def criar_questoes_em_lote(itens):
    """
    itens: lista de dicts com chaves:
      area, subtopico (opcional), enunciado, alternativas (dict),
      resposta_correta, explicacao (opcional), banca (opcional), ano (opcional)

    Cria áreas/subtópicos que ainda não existirem. Retorna (inseridos, erros),
    onde erros é uma lista de (indice, mensagem) para linhas que falharam
    (as demais linhas continuam sendo importadas normalmente).
    """
    area_cache = {}
    sub_cache = {}
    inseridos = 0
    erros = []
    with get_conn() as conn:
        c = conn.cursor()
        for idx, item in enumerate(itens):
            try:
                area_nome = str(item["area"]).strip()
                if not area_nome:
                    raise ValueError("área vazia")
                if area_nome not in area_cache:
                    row = c.execute("SELECT id FROM areas WHERE nome = ?", (area_nome,)).fetchone()
                    if row:
                        area_cache[area_nome] = row["id"]
                    else:
                        c.execute("INSERT INTO areas (nome) VALUES (?)", (area_nome,))
                        area_cache[area_nome] = c.lastrowid
                area_id = area_cache[area_nome]

                subtopico_nome = str(item.get("subtopico") or "").strip() or None
                subtopico_id = None
                if subtopico_nome:
                    chave = (area_id, subtopico_nome)
                    if chave not in sub_cache:
                        row = c.execute(
                            "SELECT id FROM subtopicos WHERE area_id = ? AND nome = ?",
                            (area_id, subtopico_nome),
                        ).fetchone()
                        if row:
                            sub_cache[chave] = row["id"]
                        else:
                            c.execute(
                                "INSERT INTO subtopicos (area_id, nome) VALUES (?, ?)",
                                (area_id, subtopico_nome),
                            )
                            sub_cache[chave] = c.lastrowid
                    subtopico_id = sub_cache[chave]

                if not item.get("enunciado"):
                    raise ValueError("enunciado vazio")
                if not item.get("alternativas") or len(item["alternativas"]) < 2:
                    raise ValueError("menos de 2 alternativas")
                if item.get("resposta_correta") not in item["alternativas"]:
                    raise ValueError("resposta_correta não corresponde a nenhuma alternativa")

                c.execute("""
                    INSERT INTO questoes
                        (area_id, subtopico_id, enunciado, alternativas, resposta_correta,
                         explicacao, banca, ano, criada_em)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    area_id, subtopico_id, item["enunciado"],
                    json.dumps(item["alternativas"], ensure_ascii=False),
                    item["resposta_correta"], item.get("explicacao", ""),
                    item.get("banca", ""), item.get("ano"),
                    datetime.datetime.now().isoformat(),
                ))
                inseridos += 1
            except Exception as e:
                erros.append((idx, str(e)))
        conn.commit()
    return inseridos, erros


def criar_materiais_em_lote(itens):
    """
    itens: lista de dicts {area, subtopico (opcional), tipo, titulo, link}
    Cria áreas/subtópicos que ainda não existirem. Retorna (inseridos, erros).
    """
    area_cache = {}
    sub_cache = {}
    inseridos = 0
    erros = []
    with get_conn() as conn:
        c = conn.cursor()
        for idx, item in enumerate(itens):
            try:
                area_nome = str(item["area"]).strip()
                if not area_nome:
                    raise ValueError("área vazia")
                if not item.get("titulo"):
                    raise ValueError("título vazio")
                if not item.get("link"):
                    raise ValueError("link vazio")

                if area_nome not in area_cache:
                    row = c.execute("SELECT id FROM areas WHERE nome = ?", (area_nome,)).fetchone()
                    if row:
                        area_cache[area_nome] = row["id"]
                    else:
                        c.execute("INSERT INTO areas (nome) VALUES (?)", (area_nome,))
                        area_cache[area_nome] = c.lastrowid
                area_id = area_cache[area_nome]

                subtopico_nome = str(item.get("subtopico") or "").strip() or None
                subtopico_id = None
                if subtopico_nome:
                    chave = (area_id, subtopico_nome)
                    if chave not in sub_cache:
                        row = c.execute(
                            "SELECT id FROM subtopicos WHERE area_id = ? AND nome = ?",
                            (area_id, subtopico_nome),
                        ).fetchone()
                        if row:
                            sub_cache[chave] = row["id"]
                        else:
                            c.execute(
                                "INSERT INTO subtopicos (area_id, nome) VALUES (?, ?)",
                                (area_id, subtopico_nome),
                            )
                            sub_cache[chave] = c.lastrowid
                    subtopico_id = sub_cache[chave]

                c.execute("""
                    INSERT INTO materiais (area_id, subtopico_id, tipo, titulo, link_mediafire)
                    VALUES (?, ?, ?, ?, ?)
                """, (area_id, subtopico_id, item.get("tipo") or "Outro", item["titulo"], item["link"]))
                inseridos += 1
            except Exception as e:
                erros.append((idx, str(e)))
        conn.commit()
    return inseridos, erros


# ---------------------------------------------------------------------------
# Materiais (MediaFire) - CRUD individual
# ---------------------------------------------------------------------------

def criar_material(area_id, subtopico_id, tipo, titulo, link_mediafire, mediafire_key=None):
    """Insere um material. Se `mediafire_key` já existir no banco (mesmo
    arquivo importado antes), a inserção é ignorada silenciosamente —
    isso é o que torna a sincronização com o MediaFire segura para
    rodar várias vezes sem duplicar nada.

    Retorna True se um novo registro foi inserido, False se foi ignorado
    por já existir (duplicado).
    """
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO materiais
                (area_id, subtopico_id, tipo, titulo, link_mediafire, mediafire_key, sincronizado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (mediafire_key) WHERE mediafire_key IS NOT NULL DO NOTHING
        """, (
            area_id, subtopico_id, tipo, titulo, link_mediafire, mediafire_key,
            datetime.datetime.now().isoformat() if mediafire_key else None,
        ))
        return cur.rowcount > 0


def contar_materiais():
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) AS n FROM materiais").fetchone()["n"]


def _clausulas_filtro_materiais(area_id, subtopico_id, tipo, busca):
    condicoes = ["1=1"]
    params = []
    if area_id:
        condicoes.append("area_id = ?")
        params.append(area_id)
    if subtopico_id:
        condicoes.append("subtopico_id = ?")
        params.append(subtopico_id)
    if tipo:
        condicoes.append("tipo = ?")
        params.append(tipo)
    if busca:
        condicoes.append("titulo LIKE ?")
        params.append(f"%{busca}%")
    return " AND ".join(condicoes), params


def listar_materiais(area_id=None, subtopico_id=None):
    """Mantido para compatibilidade; para telas com muitos itens, prefira
    listar_materiais_paginado (evita carregar milhares de linhas de uma vez)."""
    query = "SELECT * FROM materiais WHERE 1=1"
    params = []
    if area_id:
        query += " AND area_id = ?"
        params.append(area_id)
    if subtopico_id:
        query += " AND subtopico_id = ?"
        params.append(subtopico_id)
    query += " ORDER BY tipo, titulo"
    with get_conn() as conn:
        return conn.execute(query, params).fetchall()


def listar_materiais_paginado(area_id=None, subtopico_id=None, tipo=None, busca=None,
                               limite=50, offset=0):
    condicao, params = _clausulas_filtro_materiais(area_id, subtopico_id, tipo, busca)
    query = f"SELECT * FROM materiais WHERE {condicao} ORDER BY tipo, titulo LIMIT ? OFFSET ?"
    with get_conn() as conn:
        return conn.execute(query, params + [limite, offset]).fetchall()


def contar_materiais_filtrados(area_id=None, subtopico_id=None, tipo=None, busca=None):
    condicao, params = _clausulas_filtro_materiais(area_id, subtopico_id, tipo, busca)
    query = f"SELECT COUNT(*) AS n FROM materiais WHERE {condicao}"
    with get_conn() as conn:
        return conn.execute(query, params).fetchone()["n"]


def listar_tipos_materiais():
    with get_conn() as conn:
        rows = conn.execute("SELECT DISTINCT tipo FROM materiais ORDER BY tipo").fetchall()
        return [r["tipo"] for r in rows]


def excluir_material(material_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM materiais WHERE id = ?", (material_id,))


# ---------------------------------------------------------------------------
# Cache local dos arquivos do MediaFire
# ---------------------------------------------------------------------------

def obter_material(material_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM materiais WHERE id = ?", (material_id,)
        ).fetchone()


def registrar_cache_material(material_id, arquivo_local, tamanho_bytes):
    with get_conn() as conn:
        conn.execute("""
            UPDATE materiais
            SET arquivo_local = ?, tamanho_bytes = ?, cache_atualizado_em = ?
            WHERE id = ?
        """, (arquivo_local, tamanho_bytes, datetime.datetime.now().isoformat(), material_id))


def limpar_cache_material(material_id):
    with get_conn() as conn:
        conn.execute("""
            UPDATE materiais
            SET arquivo_local = NULL, tamanho_bytes = NULL, cache_atualizado_em = NULL
            WHERE id = ?
        """, (material_id,))


def estatisticas_cache():
    with get_conn() as conn:
        row = conn.execute("""
            SELECT COUNT(*) AS n, COALESCE(SUM(tamanho_bytes), 0) AS bytes_total
            FROM materiais WHERE arquivo_local IS NOT NULL
        """).fetchone()
        return row["n"], row["bytes_total"]


# ---------------------------------------------------------------------------
# Simulados (provas cronometradas)
# ---------------------------------------------------------------------------

def listar_bancas():
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT DISTINCT banca FROM questoes
            WHERE banca IS NOT NULL AND TRIM(banca) != ''
            ORDER BY banca
        """).fetchall()
        return [r["banca"] for r in rows]


def _clausulas_filtro_simulado(area_id, banca):
    condicoes = ["1=1"]
    params = []
    if area_id:
        condicoes.append("area_id = ?")
        params.append(area_id)
    if banca:
        condicoes.append("banca = ?")
        params.append(banca)
    return " AND ".join(condicoes), params


def contar_questoes_disponiveis(area_id=None, banca=None):
    condicao, params = _clausulas_filtro_simulado(area_id, banca)
    with get_conn() as conn:
        return conn.execute(
            f"SELECT COUNT(*) AS n FROM questoes WHERE {condicao}", params
        ).fetchone()["n"]


def questoes_aleatorias(area_id=None, banca=None, limite=10):
    condicao, params = _clausulas_filtro_simulado(area_id, banca)
    query = f"SELECT * FROM questoes WHERE {condicao} ORDER BY RANDOM() LIMIT ?"
    with get_conn() as conn:
        return conn.execute(query, params + [limite]).fetchall()


def criar_simulado(area_id, banca, num_questoes, tempo_limite_min, questao_ids, *, usuario_id):
    """Cria o registro do simulado e seus itens (na ordem sorteada em
    `questao_ids`). Retorna o id do simulado criado."""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO simulados
                (usuario_id, area_id, banca, num_questoes, tempo_limite_min, iniciado_em)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (usuario_id, area_id, banca or None, num_questoes, tempo_limite_min,
              datetime.datetime.now().isoformat()))
        simulado_id = c.lastrowid
        for ordem, questao_id in enumerate(questao_ids):
            c.execute("""
                INSERT INTO simulado_itens (simulado_id, questao_id, ordem)
                VALUES (?, ?, ?)
            """, (simulado_id, questao_id, ordem))
        return simulado_id


def registrar_resposta_simulado(simulado_id, questao_id, resposta_dada, *, usuario_id):
    """Grava (ou atualiza) a resposta escolhida para uma questão do
    simulado, sem revelar se está certa — isso só é usado na tela de
    resultado. Idempotente: pode ser chamada de novo a cada render."""
    with get_conn() as conn:
        dono = conn.execute(
            "SELECT id FROM simulados WHERE id = ? AND usuario_id = ?", (simulado_id, usuario_id)
        ).fetchone()
        if dono is None:
            raise PermissionError("Simulado não encontrado ou não pertence a este usuário.")
        questao = conn.execute(
            "SELECT resposta_correta FROM questoes WHERE id = ?", (questao_id,)
        ).fetchone()
        correta = int(resposta_dada == questao["resposta_correta"])
        conn.execute("""
            UPDATE simulado_itens
            SET resposta_dada = ?, correta = ?
            WHERE simulado_id = ? AND questao_id = ?
        """, (resposta_dada, correta, simulado_id, questao_id))


def finalizar_simulado(simulado_id, *, usuario_id):
    """Agrega os resultados e marca o simulado como finalizado. Deve ser
    chamada uma única vez, no momento em que o simulado termina (por
    tempo esgotado ou pelo botão 'Finalizar')."""
    with get_conn() as conn:
        dono = conn.execute(
            "SELECT id FROM simulados WHERE id = ? AND usuario_id = ?", (simulado_id, usuario_id)
        ).fetchone()
        if dono is None:
            raise PermissionError("Simulado não encontrado ou não pertence a este usuário.")
        agregado = conn.execute("""
            SELECT COUNT(*) AS total_respondidas, SUM(correta) AS acertos
            FROM simulado_itens
            WHERE simulado_id = ? AND resposta_dada IS NOT NULL
        """, (simulado_id,)).fetchone()
        conn.execute("""
            UPDATE simulados
            SET acertos = ?, total_respondidas = ?, finalizado_em = ?
            WHERE id = ?
        """, (
            agregado["acertos"] or 0, agregado["total_respondidas"] or 0,
            datetime.datetime.now().isoformat(), simulado_id,
        ))


def obter_simulado(simulado_id, *, usuario_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM simulados WHERE id = ? AND usuario_id = ?", (simulado_id, usuario_id)
        ).fetchone()


def listar_itens_simulado(simulado_id, *, usuario_id):
    with get_conn() as conn:
        return conn.execute("""
            SELECT si.id AS item_id, si.ordem, si.resposta_dada, si.correta,
                   q.*
            FROM simulado_itens si
            JOIN questoes q ON q.id = si.questao_id
            JOIN simulados s ON s.id = si.simulado_id
            WHERE si.simulado_id = ? AND s.usuario_id = ?
            ORDER BY si.ordem
        """, (simulado_id, usuario_id)).fetchall()


def desempenho_simulado(simulado_id, *, usuario_id):
    """Mesma forma de `desempenho_por_area`, mas escopada a um simulado.
    Conta TODOS os itens (não só os respondidos) — questão em branco
    pesa como erro, igual numa prova de verdade."""
    with get_conn() as conn:
        return conn.execute("""
            SELECT a.nome AS area,
                   COUNT(si.id) AS total,
                   SUM(COALESCE(si.correta, 0)) AS acertos,
                   ROUND(100.0 * SUM(COALESCE(si.correta, 0)) / COUNT(si.id), 1) AS pct_acerto
            FROM simulado_itens si
            JOIN questoes q ON q.id = si.questao_id
            JOIN areas a ON a.id = q.area_id
            JOIN simulados s ON s.id = si.simulado_id
            WHERE si.simulado_id = ? AND s.usuario_id = ?
            GROUP BY a.nome
            ORDER BY pct_acerto ASC
        """, (simulado_id, usuario_id)).fetchall()


def listar_simulados(limite=10, *, usuario_id):
    with get_conn() as conn:
        return conn.execute("""
            SELECT s.*, a.nome AS area,
                   ROUND(100.0 * s.acertos / s.num_questoes, 1) AS pct_acerto
            FROM simulados s
            LEFT JOIN areas a ON a.id = s.area_id
            WHERE s.finalizado_em IS NOT NULL AND s.usuario_id = ?
            ORDER BY s.finalizado_em DESC
            LIMIT ?
        """, (usuario_id, limite)).fetchall()


# ---------------------------------------------------------------------------
# Usuários / autenticação
# ---------------------------------------------------------------------------

def criar_usuario(email, senha_hash):
    """Cria um novo usuário. Retorna o id criado, ou None se o e-mail já
    estiver cadastrado."""
    email = email.strip().lower()
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO usuarios (email, senha_hash, criado_em) VALUES (?, ?, ?)",
                (email, senha_hash, datetime.datetime.now().isoformat()),
            )
            return cur.lastrowid
    except psycopg2.errors.UniqueViolation:
        return None


def obter_usuario_por_email(email):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM usuarios WHERE email = ?", (email.strip().lower(),)
        ).fetchone()


def obter_usuario(usuario_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
