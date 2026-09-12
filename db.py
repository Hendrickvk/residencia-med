"""
Camada de acesso ao banco de dados (Postgres) da plataforma de preparação
para residência médica.

Todas as tabelas e funções de CRUD/consulta usadas pelo app Streamlit
ficam centralizadas aqui, para manter a interface (app.py) enxuta.
"""

import os
import json
import datetime
import threading
from contextlib import contextmanager

import psycopg2
import psycopg2.errors
import psycopg2.extensions
import psycopg2.pool
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


# Pool de conexões: abrir uma conexão nova ao Postgres custa ~200-250ms
# (handshake TCP+TLS+autenticação, mais ainda se o Neon tiver "dormido"
# por inatividade), contra ~20ms pra reaproveitar uma conexão já aberta —
# medido contra o banco de produção. Como quase toda função deste arquivo
# abre sua própria conexão via `with get_conn()`, e uma única página pode
# chamar várias dessas funções, sem pool cada clique no menu abria de 2 a
# 10 conexões novas do zero — é isso que fazia a navegação parecer lenta.
# O pool é um único objeto por processo (módulo), compartilhado entre
# todas as sessões/usuários que essa instância do Streamlit atender.
_pool = None
_pool_lock = threading.Lock()


def _get_pool():
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = psycopg2.pool.ThreadedConnectionPool(1, 10, _database_url())
    return _pool


@contextmanager
def get_conn():
    # Importante: código que precisa capturar uma exceção de SQL e
    # continuar (ex: criar_usuario, para tratar e-mail duplicado) tem
    # que deixar a exceção propagar para FORA deste `with` inteiro — se
    # for capturada por dentro do `with`, a função segue normalmente e o
    # conn.commit() abaixo roda em cima de uma transação já abortada
    # pelo Postgres (InFailedSqlTransaction).
    pool = _get_pool()
    raw_conn = pool.getconn()
    conn = _PGConnection(raw_conn)
    try:
        yield conn
        conn.commit()
    except Exception:
        # limpa o estado de transação abortada antes de devolver a conexão
        # pro pool — senão o próximo a pegar essa conexão emperra em
        # InFailedSqlTransaction logo na primeira query.
        raw_conn.rollback()
        raise
    finally:
        pool.putconn(raw_conn)


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
            proxima_revisao TIMESTAMP NOT NULL,
            PRIMARY KEY (usuario_id, questao_id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
            FOREIGN KEY (questao_id) REFERENCES questoes(id) ON DELETE CASCADE
        )
        """)

        # Questões marcadas manualmente pelo aluno durante uma sessão de
        # prática ("Marcar para revisão") — sinal independente do SM-2
        # (que já agenda revisão automática pra erros): aqui é o aluno
        # dizendo "quero rever isso", mesmo tendo acertado.
        c.execute("""
        CREATE TABLE IF NOT EXISTS questoes_marcadas (
            usuario_id INTEGER NOT NULL,
            questao_id INTEGER NOT NULL,
            criada_em TEXT NOT NULL,
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

        # Migração leve: imagem da questão (raio-X, ECG, gráfico, foto clínica
        # etc.) guardada como bytes direto no Postgres — não em disco, porque
        # o Streamlit Community Cloud apaga o filesystem local a cada deploy.
        c.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'questoes'
        """)
        colunas_questoes = {row["column_name"] for row in c.fetchall()}
        if "imagem" not in colunas_questoes:
            c.execute("ALTER TABLE questoes ADD COLUMN imagem BYTEA")
        if "imagem_mime" not in colunas_questoes:
            c.execute("ALTER TABLE questoes ADD COLUMN imagem_mime TEXT")

        # Migração leve: preferência de tema (claro/escuro) e data da prova
        # alvo, usadas pelo redesign visual (alternador de tema no topo,
        # contagem regressiva na barra superior).
        c.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'usuarios'
        """)
        colunas_usuarios = {row["column_name"] for row in c.fetchall()}
        if "tema" not in colunas_usuarios:
            c.execute("ALTER TABLE usuarios ADD COLUMN tema TEXT NOT NULL DEFAULT 'light'")
        if "data_prova_alvo" not in colunas_usuarios:
            c.execute("ALTER TABLE usuarios ADD COLUMN data_prova_alvo TEXT")

        # Migração leve: calibração de confiança ("acertei com segurança" /
        # "acertei no chute"), usada para ajustar a qualidade informada ao
        # SM-2 além do simples certo/errado.
        c.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'respostas'
        """)
        colunas_respostas = {row["column_name"] for row in c.fetchall()}
        if "confianca" not in colunas_respostas:
            c.execute("ALTER TABLE respostas ADD COLUMN confianca TEXT")

        # Migração leve: tempo gasto na questão (cronômetro por questão da
        # API/frontend novo — o Streamlit nunca mediu isso por questão,
        # só a duração da sessão inteira).
        if "tempo_ms" not in colunas_respostas:
            c.execute("ALTER TABLE respostas ADD COLUMN tempo_ms INTEGER")

        # Migração: proxima_revisao era só data (TEXT), sem hora — por isso
        # "Errei — 10 min" na Revisão Espaçada sempre pulava pro dia
        # seguinte de verdade no banco (só voltava "logo" via um hack no
        # session_state do Streamlit). Convertida pra TIMESTAMP; valores
        # existentes ('2026-09-10') viram meia-noite daquele dia, que é o
        # comportamento conservador equivalente ao que já valia antes.
        c.execute("""
            SELECT data_type FROM information_schema.columns
            WHERE table_name = 'revisao' AND column_name = 'proxima_revisao'
        """)
        tipo_atual = c.fetchone()
        if tipo_atual and tipo_atual["data_type"] != "timestamp without time zone":
            c.execute("""
                ALTER TABLE revisao ALTER COLUMN proxima_revisao
                TYPE TIMESTAMP USING proxima_revisao::timestamp
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

        # Postgres não indexa colunas de FK automaticamente (só o lado
        # referenciado/PK ganha índice). Sem isso, toda query do Dashboard
        # (JOIN respostas->questoes->areas filtrando por usuario_id/banca)
        # faz sequential scan — cresce junto com o histórico de respostas.
        c.execute("CREATE INDEX IF NOT EXISTS idx_respostas_usuario_id ON respostas(usuario_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_respostas_questao_id ON respostas(questao_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_questoes_area_id ON questoes(area_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_questoes_banca ON questoes(banca)")

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


def atualizar_questao(questao_id, area_id, subtopico_id, enunciado, alternativas: dict,
                       resposta_correta, explicacao="", banca="", ano=None):
    with get_conn() as conn:
        conn.execute("""
            UPDATE questoes
            SET area_id = ?, subtopico_id = ?, enunciado = ?, alternativas = ?,
                resposta_correta = ?, explicacao = ?, banca = ?, ano = ?
            WHERE id = ?
        """, (
            area_id, subtopico_id, enunciado, json.dumps(alternativas, ensure_ascii=False),
            resposta_correta, explicacao, banca, ano, questao_id,
        ))


def listar_anos():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT ano FROM questoes WHERE ano IS NOT NULL ORDER BY ano DESC"
        ).fetchall()
        return [r["ano"] for r in rows]


def ids_questoes_filtro_pratica(*, usuario_id, area_id=None, subtopico_id=None,
                                 banca=None, ano=None, apenas_erros=False,
                                 excluir_respondidas=False):
    """Configurador de Praticar (REDESIGN.md §4.2): filtros combináveis além
    de área/subtópico — banca, ano, e dois interruptores que olham o
    histórico de respostas do próprio usuário."""
    condicoes = ["1=1"]
    params = []
    if area_id:
        condicoes.append("q.area_id = ?")
        params.append(area_id)
    if subtopico_id:
        condicoes.append("q.subtopico_id = ?")
        params.append(subtopico_id)
    if banca:
        condicoes.append("q.banca = ?")
        params.append(banca)
    if ano:
        condicoes.append("q.ano = ?")
        params.append(ano)
    if apenas_erros:
        condicoes.append(
            "EXISTS (SELECT 1 FROM respostas r WHERE r.questao_id = q.id "
            "AND r.usuario_id = ? AND r.correta = 0)"
        )
        params.append(usuario_id)
    if excluir_respondidas:
        condicoes.append(
            "NOT EXISTS (SELECT 1 FROM respostas r WHERE r.questao_id = q.id AND r.usuario_id = ?)"
        )
        params.append(usuario_id)
    query = f"SELECT q.id FROM questoes q WHERE {' AND '.join(condicoes)}"
    with get_conn() as conn:
        return [row["id"] for row in conn.execute(query, params).fetchall()]


def obter_questoes_por_ids(ids, *, usuario_id):
    """Busca N questões completas (com gabarito, comentário e o estado
    'marcada' do usuário) a partir de uma lista de ids, preservando a ORDEM
    da lista recebida — crucial porque o chamador já embaralhou/cortou essa
    lista (fila de uma sessão de Praticar). Essa função não existia antes da
    migração para API: o Streamlit buscava uma questão de cada vez conforme
    o aluno avançava (`obter_questao`), o que é incompatível com o requisito
    de feedback instantâneo (MIGRACAO.md §2) porque exigiria uma chamada de
    rede por questão."""
    ids = list(ids)
    if not ids:
        return []
    placeholders = ",".join(["?"] * len(ids))
    query = f"""
        SELECT q.*, a.nome AS area, s.nome AS subtopico,
               (m.usuario_id IS NOT NULL) AS marcada
        FROM questoes q
        JOIN areas a ON a.id = q.area_id
        LEFT JOIN subtopicos s ON s.id = q.subtopico_id
        LEFT JOIN questoes_marcadas m ON m.questao_id = q.id AND m.usuario_id = ?
        WHERE q.id IN ({placeholders})
    """
    with get_conn() as conn:
        rows = conn.execute(query, [usuario_id] + ids).fetchall()
    por_id = {r["id"]: r for r in rows}
    return [por_id[i] for i in ids if i in por_id]


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
        condicoes.append("enunciado ILIKE ?")
        params.append(f"%{busca}%")
    return " AND ".join(condicoes), params


def listar_questoes_paginado(area_id=None, subtopico_id=None, busca=None, limite=50, offset=0):
    condicao, params = _clausulas_filtro_questoes(area_id, subtopico_id, busca)
    condicao = condicao.replace("area_id", "q.area_id").replace("subtopico_id", "q.subtopico_id")
    query = f"""
        SELECT q.*, a.nome AS area
        FROM questoes q JOIN areas a ON a.id = q.area_id
        WHERE {condicao} ORDER BY q.criada_em DESC LIMIT ? OFFSET ?
    """
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


def busca_global(termo, limite=10):
    """Implementa a busca do topbar (MIGRACAO.md §5): hoje o campo existe
    na tela mas não consulta nada — 'pior que não existir', segundo o
    próprio documento de migração. `LIKE` simples em enunciado de questão
    e título de material, agrupado por tipo."""
    termo = f"%{termo}%"
    with get_conn() as conn:
        questoes = conn.execute("""
            SELECT q.id, q.enunciado, a.nome AS area
            FROM questoes q JOIN areas a ON a.id = q.area_id
            WHERE q.enunciado ILIKE ? ORDER BY q.criada_em DESC LIMIT ?
        """, (termo, limite)).fetchall()
        materiais = conn.execute("""
            SELECT id, titulo, tipo, link_mediafire FROM materiais
            WHERE titulo ILIKE ? ORDER BY titulo LIMIT ?
        """, (termo, limite)).fetchall()
    return {"questoes": questoes, "materiais": materiais}


def contar_questoes():
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) AS n FROM questoes").fetchone()["n"]


def obter_questao(questao_id):
    with get_conn() as conn:
        return conn.execute("""
            SELECT q.*, a.nome AS area, s.nome AS subtopico
            FROM questoes q
            JOIN areas a ON a.id = q.area_id
            LEFT JOIN subtopicos s ON s.id = q.subtopico_id
            WHERE q.id = ?
        """, (questao_id,)).fetchone()


def excluir_questao(questao_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM questoes WHERE id = ?", (questao_id,))


def definir_imagem_questao(questao_id, imagem_bytes, mime_type):
    """Anexa/substitui a imagem de uma questão (raio-X, ECG, gráfico, foto
    clínica etc.), guardada como bytes direto no Postgres via psycopg2.Binary
    — evita depender do filesystem local, que o Streamlit Community Cloud
    apaga a cada deploy."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE questoes SET imagem = ?, imagem_mime = ? WHERE id = ?",
            (psycopg2.Binary(imagem_bytes), mime_type, questao_id),
        )


def remover_imagem_questao(questao_id):
    with get_conn() as conn:
        conn.execute(
            "UPDATE questoes SET imagem = NULL, imagem_mime = NULL WHERE id = ?",
            (questao_id,),
        )


# ---------------------------------------------------------------------------
# Respostas / desempenho
# ---------------------------------------------------------------------------

def registrar_resposta(questao_id, resposta_dada, correta: bool, *, usuario_id, confianca=None, tempo_ms=None):
    """`confianca`: None (não perguntado), 'seguro' ou 'chute' — calibração
    exibida só quando o aluno acerta, usada para ajustar a qualidade
    enviada ao SM-2 além do simples certo/errado."""
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO respostas (usuario_id, questao_id, resposta_dada, correta, respondida_em, confianca, tempo_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (usuario_id, questao_id, resposta_dada, int(correta), datetime.datetime.now().isoformat(), confianca, tempo_ms))


def distribuicao_respostas_questao(questao_id, *, excluir_usuario_id=None):
    """% de escolha de cada alternativa entre todas as respostas já dadas
    a essa questão (por qualquer usuário) — usado pra mostrar a barra fina
    de 'percentual dos demais usuários' em cada alternativa no modo
    interativo. `excluir_usuario_id` tira a própria resposta do aluno atual
    da conta, pra o rótulo continuar correto ('demais usuários')."""
    query = "SELECT resposta_dada, COUNT(*) AS total FROM respostas WHERE questao_id = ?"
    params = [questao_id]
    if excluir_usuario_id is not None:
        query += " AND usuario_id != ?"
        params.append(excluir_usuario_id)
    query += " GROUP BY resposta_dada"
    with get_conn() as conn:
        linhas = conn.execute(query, params).fetchall()
    total = sum(r["total"] for r in linhas)
    if not total:
        return {}
    return {r["resposta_dada"]: round(100 * r["total"] / total, 1) for r in linhas}


def contar_respondidas_hoje(*, usuario_id):
    with get_conn() as conn:
        row = conn.execute("""
            SELECT COUNT(*) AS total FROM respostas
            WHERE usuario_id = ? AND respondida_em::date = CURRENT_DATE
        """, (usuario_id,)).fetchone()
        return row["total"] if row else 0


def calcular_ofensiva(*, usuario_id):
    """Dias consecutivos com pelo menos 1 resposta registrada, contando pra
    trás a partir de hoje (ou de ontem, se hoje ainda não tem resposta —
    a ofensiva de ontem continua 'valendo' até o fim do dia de hoje).
    Retorna (dias_consecutivos, respondeu_hoje)."""
    with get_conn() as conn:
        linhas = conn.execute("""
            SELECT DISTINCT (respondida_em::date) AS dia
            FROM respostas WHERE usuario_id = ?
        """, (usuario_id,)).fetchall()
    dias = {r["dia"] for r in linhas}
    hoje = datetime.date.today()
    respondeu_hoje = hoje in dias
    cursor = hoje if respondeu_hoje else hoje - datetime.timedelta(days=1)
    streak = 0
    while cursor in dias:
        streak += 1
        cursor -= datetime.timedelta(days=1)
    return streak, respondeu_hoje


def definir_prova_alvo(usuario_id, data_iso: str | None):
    """`data_iso`: 'YYYY-MM-DD' ou None pra limpar."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE usuarios SET data_prova_alvo = ? WHERE id = ?",
            (data_iso, usuario_id),
        )


def atualizar_tema_usuario(usuario_id, tema: str):
    with get_conn() as conn:
        conn.execute("UPDATE usuarios SET tema = ? WHERE id = ?", (tema, usuario_id))


def marcar_questao(usuario_id, questao_id):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO questoes_marcadas (usuario_id, questao_id, criada_em)
            VALUES (?, ?, ?)
            ON CONFLICT (usuario_id, questao_id) DO NOTHING
        """, (usuario_id, questao_id, datetime.datetime.now().isoformat()))


def desmarcar_questao(usuario_id, questao_id):
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM questoes_marcadas WHERE usuario_id = ? AND questao_id = ?",
            (usuario_id, questao_id),
        )


def questao_esta_marcada(usuario_id, questao_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM questoes_marcadas WHERE usuario_id = ? AND questao_id = ?",
            (usuario_id, questao_id),
        ).fetchone()
        return row is not None


def listar_questoes_marcadas(*, usuario_id):
    with get_conn() as conn:
        return conn.execute("""
            SELECT q.* FROM questoes_marcadas m
            JOIN questoes q ON q.id = m.questao_id
            WHERE m.usuario_id = ?
            ORDER BY m.criada_em DESC
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


def desempenho_dashboard_combinado(*, usuario_id):
    """Substitui as antigas desempenho_por_area + desempenho_por_banca +
    desempenho_por_banca_e_area + contar_respostas_sem_banca — mesmas 4
    queries de sempre, mas embrulhadas em subqueries jsonb_agg dentro de
    um único SELECT, pra viajarem num só round-trip ao Postgres em vez
    de 4 sequenciais (era o gargalo que sobrava depois do cache: toda
    vez que o cache expira, o Dashboard pagava 4x a latência de rede até
    o Neon, uma atrás da outra)."""
    with get_conn() as conn:
        row = conn.execute("""
            SELECT
              (SELECT jsonb_agg(t) FROM (
                  SELECT a.id AS area_id, a.nome AS area,
                         COUNT(r.id) AS total,
                         SUM(r.correta) AS acertos,
                         ROUND(100.0 * SUM(r.correta) / COUNT(r.id), 1) AS pct_acerto
                  FROM respostas r
                  JOIN questoes q ON q.id = r.questao_id
                  JOIN areas a ON a.id = q.area_id
                  WHERE r.usuario_id = ?
                  GROUP BY a.id, a.nome
                  ORDER BY pct_acerto ASC
              ) t) AS por_area,
              (SELECT jsonb_agg(t) FROM (
                  SELECT q.banca AS banca,
                         COUNT(r.id) AS total,
                         SUM(r.correta) AS acertos,
                         ROUND(100.0 * SUM(r.correta) / COUNT(r.id), 1) AS pct_acerto
                  FROM respostas r
                  JOIN questoes q ON q.id = r.questao_id
                  WHERE q.banca IS NOT NULL AND TRIM(q.banca) != '' AND r.usuario_id = ?
                  GROUP BY q.banca
                  ORDER BY pct_acerto ASC
              ) t) AS por_banca,
              (SELECT jsonb_agg(t) FROM (
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
              ) t) AS por_banca_area,
              (SELECT COUNT(*)
                  FROM respostas r
                  JOIN questoes q ON q.id = r.questao_id
                  WHERE (q.banca IS NULL OR TRIM(q.banca) = '') AND r.usuario_id = ?
              ) AS sem_banca
        """, (usuario_id, usuario_id, usuario_id, usuario_id)).fetchone()
        return {
            "por_area": row["por_area"] or [],
            "por_banca": row["por_banca"] or [],
            "por_banca_area": row["por_banca_area"] or [],
            "sem_banca": row["sem_banca"] or 0,
        }


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


def ultima_sincronizacao():
    with get_conn() as conn:
        row = conn.execute(
            "SELECT MAX(sincronizado_em) AS ult FROM materiais WHERE sincronizado_em IS NOT NULL"
        ).fetchone()
        return row["ult"] if row else None


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
        condicoes.append("titulo ILIKE ?")
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
    condicao = condicao.replace("area_id", "m.area_id")
    query = f"""
        SELECT m.*, s.nome AS subtopico
        FROM materiais m LEFT JOIN subtopicos s ON s.id = m.subtopico_id
        WHERE {condicao} ORDER BY m.tipo, m.titulo LIMIT ? OFFSET ?
    """
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


def excluir_todos_materiais():
    """Apaga TODOS os materiais cadastrados — ação irreversível, usada
    pela 'zona de risco' da tela de Materiais de Estudo (com confirmação
    explícita do usuário antes de chamar isso)."""
    with get_conn() as conn:
        conn.execute("DELETE FROM materiais")


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
    """Inclui o estado `marcada` (tabela `questoes_marcadas`, a mesma do
    Praticar) — é o que sustenta o terceiro estado da grade de navegação do
    Simulado (respondida/marcada/em branco), dívida registrada no
    HANDOFF_REDESIGN.md e resolvida na Fase 5 do MIGRACAO.md."""
    with get_conn() as conn:
        return conn.execute("""
            SELECT si.id AS item_id, si.ordem, si.resposta_dada, si.correta,
                   q.*, (m.usuario_id IS NOT NULL) AS marcada
            FROM simulado_itens si
            JOIN questoes q ON q.id = si.questao_id
            JOIN simulados s ON s.id = si.simulado_id
            LEFT JOIN questoes_marcadas m ON m.questao_id = q.id AND m.usuario_id = ?
            WHERE si.simulado_id = ? AND s.usuario_id = ?
            ORDER BY si.ordem
        """, (usuario_id, simulado_id, usuario_id)).fetchall()


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
