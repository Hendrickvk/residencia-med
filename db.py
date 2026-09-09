"""
Camada de acesso ao banco de dados (SQLite) da plataforma de preparação
para residência médica.

Todas as tabelas e funções de CRUD/consulta usadas pelo app Streamlit
ficam centralizadas aqui, para manter a interface (app.py) enxuta.
"""

import sqlite3
import os
import json
import datetime
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "residencia.db")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS subtopicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            FOREIGN KEY (area_id) REFERENCES areas(id) ON DELETE CASCADE,
            UNIQUE(area_id, nome)
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS questoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

        c.execute("""
        CREATE TABLE IF NOT EXISTS respostas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            questao_id INTEGER NOT NULL,
            resposta_dada TEXT NOT NULL,
            correta INTEGER NOT NULL,   -- 0 ou 1
            respondida_em TEXT NOT NULL,
            FOREIGN KEY (questao_id) REFERENCES questoes(id) ON DELETE CASCADE
        )
        """)

        # Preparado para o módulo de repetição espaçada (SM-2 simplificado)
        c.execute("""
        CREATE TABLE IF NOT EXISTS revisao (
            questao_id INTEGER PRIMARY KEY,
            facilidade REAL NOT NULL DEFAULT 2.5,
            intervalo_dias INTEGER NOT NULL DEFAULT 1,
            repeticoes INTEGER NOT NULL DEFAULT 0,
            proxima_revisao TEXT NOT NULL,
            FOREIGN KEY (questao_id) REFERENCES questoes(id) ON DELETE CASCADE
        )
        """)

        # Preparado para o módulo de materiais (MediaFire)
        c.execute("""
        CREATE TABLE IF NOT EXISTS materiais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        colunas_existentes = {row["name"] for row in c.execute("PRAGMA table_info(materiais)")}
        if "mediafire_key" not in colunas_existentes:
            c.execute("ALTER TABLE materiais ADD COLUMN mediafire_key TEXT")
        if "sincronizado_em" not in colunas_existentes:
            c.execute("ALTER TABLE materiais ADD COLUMN sincronizado_em TEXT")

        # Evita reimportar o mesmo arquivo do MediaFire duas vezes
        c.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_materiais_mfkey
            ON materiais(mediafire_key) WHERE mediafire_key IS NOT NULL
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
            c.execute("INSERT OR IGNORE INTO areas (nome) VALUES (?)", (nome,))
        conn.commit()


# ---------------------------------------------------------------------------
# Áreas e subtópicos
# ---------------------------------------------------------------------------

def listar_areas():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM areas ORDER BY nome").fetchall()


def criar_area(nome):
    with get_conn() as conn:
        conn.execute("INSERT OR IGNORE INTO areas (nome) VALUES (?)", (nome,))


def obter_ou_criar_area(nome):
    """Retorna o id da área, criando-a se ainda não existir. Usado pelos
    importadores em massa (planilha e MediaFire)."""
    nome = nome.strip()
    with get_conn() as conn:
        conn.execute("INSERT OR IGNORE INTO areas (nome) VALUES (?)", (nome,))
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
            "INSERT OR IGNORE INTO subtopicos (area_id, nome) VALUES (?, ?)",
            (area_id, nome),
        )


def obter_ou_criar_subtopico(area_id, nome):
    """Retorna o id do subtópico dentro da área, criando-o se necessário."""
    nome = nome.strip()
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO subtopicos (area_id, nome) VALUES (?, ?)",
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

def registrar_resposta(questao_id, resposta_dada, correta: bool):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO respostas (questao_id, resposta_dada, correta, respondida_em)
            VALUES (?, ?, ?, ?)
        """, (questao_id, resposta_dada, int(correta), datetime.datetime.now().isoformat()))


def desempenho_por_area():
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
            GROUP BY a.nome
            ORDER BY pct_acerto ASC
        """).fetchall()


def desempenho_por_subtopico(area_id=None):
    query = """
        SELECT a.nome AS area, s.nome AS subtopico,
               COUNT(r.id) AS total,
               SUM(r.correta) AS acertos,
               ROUND(100.0 * SUM(r.correta) / COUNT(r.id), 1) AS pct_acerto
        FROM respostas r
        JOIN questoes q ON q.id = r.questao_id
        JOIN areas a ON a.id = q.area_id
        LEFT JOIN subtopicos s ON s.id = q.subtopico_id
        WHERE 1=1
    """
    params = []
    if area_id:
        query += " AND q.area_id = ?"
        params.append(area_id)
    query += " GROUP BY a.nome, s.nome ORDER BY pct_acerto ASC"
    with get_conn() as conn:
        return conn.execute(query, params).fetchall()


def evolucao_diaria():
    """Total de respostas e % de acerto por dia (para gráfico de evolução)."""
    with get_conn() as conn:
        return conn.execute("""
            SELECT substr(respondida_em, 1, 10) AS dia,
                   COUNT(*) AS total,
                   SUM(correta) AS acertos,
                   ROUND(100.0 * SUM(correta) / COUNT(*), 1) AS pct_acerto
            FROM respostas
            GROUP BY dia
            ORDER BY dia ASC
        """).fetchall()


def questoes_mais_erradas(limite=15):
    with get_conn() as conn:
        return conn.execute("""
            SELECT q.id, q.enunciado, a.nome AS area,
                   COUNT(r.id) AS total_respostas,
                   SUM(CASE WHEN r.correta = 0 THEN 1 ELSE 0 END) AS erros,
                   ROUND(100.0 * SUM(CASE WHEN r.correta = 0 THEN 1 ELSE 0 END) / COUNT(r.id), 1) AS pct_erro
            FROM respostas r
            JOIN questoes q ON q.id = r.questao_id
            JOIN areas a ON a.id = q.area_id
            GROUP BY q.id
            HAVING total_respostas >= 1
            ORDER BY pct_erro DESC, total_respostas DESC
            LIMIT ?
        """, (limite,)).fetchall()


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
            INSERT OR IGNORE INTO materiais
                (area_id, subtopico_id, tipo, titulo, link_mediafire, mediafire_key, sincronizado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?)
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
