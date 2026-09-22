"""
Camada de acesso ao banco de dados (Postgres) da plataforma de preparação
para residência médica.

Todas as tabelas e funções de CRUD/consulta usadas pelo app Streamlit
ficam centralizadas aqui, para manter a interface (app.py) enxuta.
"""

import os
import re
import json
import math
import datetime
import threading
import time
import unicodedata
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


def emails_admin():
    """E-mails com poder administrativo, lidos da configuração.

    Ficavam escritos no código — `api/deps.py` e `app.py` —, e o repositório é
    público: além do spam, isso dizia a qualquer pessoa qual conta atacar para
    conseguir acesso administrativo. Sem configuração ninguém é admin, que é o
    lado seguro do erro. Mesma ordem de leitura do `_database_url`: st.secrets
    quando rodando por `streamlit run`, senão a variável de ambiente.
    """
    bruto = ""
    try:
        import streamlit as st
        if "ADMIN_EMAILS" in st.secrets:
            bruto = st.secrets["ADMIN_EMAILS"]
    except Exception:
        pass
    bruto = bruto or os.environ.get("ADMIN_EMAILS", "")
    return {e.strip().lower() for e in bruto.split(",") if e.strip()}


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


# Conexão parada no pool por mais que isso é testada antes de ser reusada. O
# Neon fecha as conexões quando suspende o compute por inatividade, e o
# psycopg2 só descobre na próxima query: sem o teste, a primeira requisição
# depois de um tempo parado falhava com "connection already closed" (e o app
# do aluno mandava a pessoa para o login).
_OCIOSIDADE_MAX_SEG = 30
_ultimo_uso = {}  # id(conexão) -> time.monotonic() de quando voltou ao pool


def _obter_conexao_viva(pool):
    for _ in range(3):
        raw_conn = pool.getconn()
        if raw_conn.closed:
            pool.putconn(raw_conn, close=True)
            continue
        ultimo = _ultimo_uso.get(id(raw_conn))
        # Sem registro = conexão recém-aberta pelo pool, não precisa de teste.
        if ultimo is None or time.monotonic() - ultimo < _OCIOSIDADE_MAX_SEG:
            return raw_conn
        try:
            with raw_conn.cursor() as cur:
                cur.execute("SELECT 1")
            raw_conn.rollback()
            return raw_conn
        except psycopg2.Error:
            # Qualquer erro no SELECT 1 = conexão inutilizável. Não só
            # OperationalError: socket SSL cortado chega como DatabaseError
            # ("SSL SYSCALL error").
            _ultimo_uso.pop(id(raw_conn), None)
            pool.putconn(raw_conn, close=True)
    return pool.getconn()


@contextmanager
def get_conn():
    # Importante: código que precisa capturar uma exceção de SQL e
    # continuar (ex: criar_usuario, para tratar e-mail duplicado) tem
    # que deixar a exceção propagar para FORA deste `with` inteiro — se
    # for capturada por dentro do `with`, a função segue normalmente e o
    # conn.commit() abaixo roda em cima de uma transação já abortada
    # pelo Postgres (InFailedSqlTransaction).
    pool = _get_pool()
    raw_conn = _obter_conexao_viva(pool)
    conn = _PGConnection(raw_conn)
    try:
        yield conn
        conn.commit()
    except Exception:
        # limpa o estado de transação abortada antes de devolver a conexão
        # pro pool — senão o próximo a pegar essa conexão emperra em
        # InFailedSqlTransaction logo na primeira query. Se a conexão caiu no
        # meio, o rollback também falha: ignora, para não esconder o erro
        # original, e o pool descarta a conexão fechada.
        if not raw_conn.closed:
            try:
                raw_conn.rollback()
            except psycopg2.Error:
                pass
        raise
    finally:
        _ultimo_uso[id(raw_conn)] = time.monotonic()
        pool.putconn(raw_conn, close=bool(raw_conn.closed))


# ---------------------------------------------------------------------------
# Taxonomia: grande área > especialidade
# ---------------------------------------------------------------------------
# As cinco grandes áreas das provas (ENAMED/Revalida) e as especialidades de
# cada uma. É a fonte única dessa lista: init_db semeia a partir daqui e o
# importador de planilha resolve nomes livres contra ela em vez de criar áreas
# novas — era assim que pastas do MediaFire como "Aprenda Nefro" viravam
# "áreas" no filtro, quando a plataforma ainda tinha materiais.
TAXONOMIA = {
    "Clínica Médica": [
        "Cardiologia", "Dermatologia", "Emergências clínicas", "Endocrinologia",
        "Gastroenterologia", "Geriatria", "Hematologia", "Hepatologia", "Infectologia",
        "Nefrologia", "Neurologia", "Oncologia e cuidados paliativos", "Pneumologia",
        "Psiquiatria", "Reumatologia",
    ],
    "Cirurgia": [
        "Cirurgia geral", "Cirurgia pediátrica", "Cirurgia vascular", "Coloproctologia",
        "Oftalmologia", "Ortopedia", "Otorrinolaringologia", "Trauma", "Urologia",
    ],
    "Ginecologia e Obstetrícia": ["Ginecologia", "Mastologia", "Obstetrícia"],
    "Pediatria": ["Infectologia pediátrica", "Neonatologia", "Pediatria clínica", "Puericultura"],
    "Medicina Preventiva e Social": [
        "Atenção primária e saúde da família", "Epidemiologia", "Ética e medicina legal",
        "Políticas de saúde e SUS", "Saúde do trabalhador", "Vigilância em saúde",
    ],
}

_CM, _CIR, _GO, _PED, _MPS = TAXONOMIA

# Terceiro nível: temas de cada especialidade, para o aluno saber exatamente o
# que a questão cobra. Agrupados a partir dos conteúdos por área da matriz do
# Revalida (Portaria Inep nº 540/2020, art. 7º) — a Matriz Comum de 2025
# (Portaria Inep nº 478/2025) só define áreas, competências e cenários, de onde
# vieram "Rede de atenção psicossocial" e "Medicina baseada em evidências".
# Viram linhas de `subtopicos`, que é UNIQUE(area_id, nome): um nome não pode se
# repetir dentro da mesma grande área.
TEMAS = {
    # Clínica Médica
    "Cardiologia": [
        "Síndrome coronariana aguda e doença isquêmica", "Insuficiência cardíaca e miocardiopatias",
        "Hipertensão arterial e emergências hipertensivas", "Arritmias",
        "Febre reumática, valvopatias e endocardite", "Doenças do pericárdio",
        "Prevenção cardiovascular e dislipidemias", "Cardiopatias congênitas no adulto",
    ],
    "Dermatologia": [
        "Hanseníase", "Infecções e infestações de pele", "Dermatoses alérgicas e farmacodermias",
        "Câncer de pele e dermatoses ocupacionais",
    ],
    "Emergências clínicas": [
        "Parada cardiorrespiratória e reanimação", "Choque e sepse",
        "Insuficiência respiratória aguda e ventilação mecânica", "Edema agudo de pulmão",
        "Distúrbios hidroeletrolíticos e ácido-base", "Intoxicações exógenas", "Via aérea e acesso venoso central",
    ],
    "Endocrinologia": [
        "Diabetes mellitus", "Doenças da tireoide e paratireoides", "Doenças da hipófise e das adrenais",
        "Obesidade",
    ],
    "Gastroenterologia": [
        "Doença do refluxo e doenças do esôfago", "Dispepsia, gastrite e doença péptica",
        "Doenças inflamatórias intestinais e diarreias", "Hemorragia digestiva", "Pancreatites",
    ],
    "Geriatria": ["Envelhecimento e avaliação geriátrica", "Grandes síndromes geriátricas", "Demências"],
    "Hematologia": [
        "Anemias carenciais e hemolíticas", "Leucemias, linfomas e mieloma",
        "Hemostasia, coagulação e trombofilias", "Hemoterapia e transfusão",
    ],
    "Hepatologia": ["Hepatites", "Cirrose e hipertensão portal", "Tumores e outras doenças do fígado"],
    "Infectologia": [
        "HIV/aids e infecções oportunistas", "Tuberculose", "Arboviroses", "Meningites e meningoencefalites",
        "Doenças parasitárias endêmicas", "Leptospirose, tétano e raiva", "Influenza e COVID-19",
        "Antimicrobianos e infecção hospitalar", "Sífilis e outras IST", "Mononucleose, febre maculosa e outras infecções",
    ],
    "Nefrologia": [
        "Lesão renal aguda", "Doença renal crônica e diálise", "Glomerulopatias", "Infecção urinária e litíase",
    ],
    "Neurologia": [
        "Doença cerebrovascular", "Epilepsias e síncope", "Cefaleias",
        "Distúrbios do movimento e doenças desmielinizantes", "Neuropatias periféricas e doenças neuromusculares",
        "Coma, estados confusionais e morte encefálica",
    ],
    "Oncologia e cuidados paliativos": [
        "Prevenção e rastreamento do câncer", "Princípios do tratamento oncológico",
        "Cuidados paliativos e terminalidade", "Complicações e emergências oncológicas",
    ],
    "Pneumologia": [
        "Asma e DPOC", "Pneumonias", "Câncer de pulmão e nódulo pulmonar", "Derrame pleural",
        "Doenças intersticiais e ocupacionais", "Tromboembolismo pulmonar",
    ],
    "Psiquiatria": [
        "Depressão e transtorno bipolar", "Transtornos de ansiedade", "Esquizofrenia e outras psicoses",
        "Uso de álcool e outras drogas", "Emergências psiquiátricas e suicídio",
        "Transtornos alimentares, somatoformes e de personalidade", "Rede de atenção psicossocial",
        "Transtornos mentais na infância e adolescência",
    ],
    "Reumatologia": [
        "Artrite reumatoide e osteoartrite", "Lúpus e outras doenças do colágeno",
        "Espondiloartrites, gota e artrites infecciosas", "Osteoporose",
        "Síndromes dolorosas da coluna e de partes moles",
    ],
    # Cirurgia
    "Cirurgia geral": [
        "Abdome agudo", "Doenças das vias biliares", "Hérnias e parede abdominal",
        "Neoplasias do aparelho digestivo", "Pré e pós-operatório e complicações cirúrgicas",
        "Cirurgia ambulatorial e feridas", "Cirurgia de cabeça e pescoço", "Cirurgia torácica", "Cirurgia bariátrica",
    ],
    "Cirurgia pediátrica": [
        "Abdome agudo na criança", "Malformações congênitas cirúrgicas", "Hérnias e afecções inguinoescrotais",
    ],
    "Cirurgia vascular": [
        "Doença arterial obstrutiva e aneurismas", "Insuficiência venosa e úlceras de membros inferiores",
        "Trombose venosa profunda e tromboembolismo",
    ],
    "Coloproctologia": ["Doenças anorretais benignas", "Câncer colorretal", "Doença diverticular e ostomias"],
    "Oftalmologia": [
        "Olho vermelho e infecções oculares", "Retinopatias", "Glaucoma e catarata", "Ametropias e estrabismo",
        "Trauma ocular e queimaduras químicas",
    ],
    "Ortopedia": [
        "Fraturas e luxações", "Infecções osteoarticulares", "Ortopedia pediátrica", "Tumores ósseos",
        "Lesões por esforço repetitivo", "Doenças da coluna vertebral",
    ],
    "Otorrinolaringologia": [
        "Otites e infecções das vias aéreas superiores", "Perda auditiva", "Rinites, obstrução nasal e disfonias",
    ],
    "Trauma": [
        "Atendimento inicial ao politraumatizado", "Traumatismo cranioencefálico e raquimedular",
        "Trauma torácico", "Trauma abdominal", "Queimaduras", "Trauma na criança, na gestante e no idoso",
        "Trauma de pelve, extremidades e partes moles",
    ],
    "Urologia": [
        "Doenças da próstata", "Tumores de rim, bexiga, testículo e pênis", "Trauma e urgências urológicas",
        "Disfunção erétil, infertilidade e bexiga neurogênica",
    ],
    # Ginecologia e Obstetrícia
    "Ginecologia": [
        "Distúrbios menstruais e sangramento uterino anormal", "Amenorreia, anovulação e hiperandrogenismo",
        "Contracepção e planejamento familiar", "Infecções genitais e IST", "Rastreamento e câncer do colo do útero",
        "Endometriose, dor pélvica e massas anexiais", "Cânceres de endométrio, ovário e vulva", "Climatério",
        "Infertilidade", "Violência sexual e contra a mulher", "Prolapso genital e incontinência urinária",
    ],
    "Mastologia": [
        "Doenças benignas da mama", "Rastreamento do câncer de mama", "Diagnóstico e tratamento do câncer de mama",
    ],
    "Obstetrícia": [
        "Pré-natal e risco gestacional", "Abortamento e gravidez ectópica",
        "Placenta prévia e descolamento prematuro", "Síndromes hipertensivas da gestação",
        "Diabetes e outras doenças clínicas na gestação", "Infecções na gestação",
        "Assistência ao parto e partograma", "Prematuridade e rotura prematura de membranas",
        "Vitalidade fetal e isoimunização", "Puerpério, hemorragia pós-parto e lactação",
    ],
    # Pediatria
    "Infectologia pediátrica": [
        "Doenças exantemáticas", "Meningites e infecções graves na criança", "Tuberculose e parasitoses na infância",
        "Infecções respiratórias agudas na criança", "Infecções gastrointestinais e urinárias na criança",
    ],
    "Neonatologia": [
        "Reanimação e cuidados ao recém-nascido", "Prematuridade e baixo peso", "Icterícia neonatal",
        "Distúrbios respiratórios do recém-nascido", "Infecções congênitas e neonatais",
        "Triagem neonatal e erros inatos do metabolismo", "Malformações e síndromes genéticas no recém-nascido",
    ],
    "Pediatria clínica": [
        "Doenças respiratórias e asma", "Diarreia e desidratação", "Distúrbios nutricionais",
        "Anemias e doenças hematológicas na infância", "Doenças renais e do trato urinário",
        "Cardiopatias congênitas e febre reumática", "Convulsões e distúrbios neurológicos",
        "Neoplasias na infância", "Saúde do adolescente", "Intoxicações e urgências pediátricas",
        "Diabetes e distúrbios endócrinos na infância", "Vasculites e doenças reumáticas na infância",
        "Desenvolvimento, comportamento e aprendizagem", "Síndromes genéticas e malformações",
        "Constipação, refluxo e outras doenças digestivas",
    ],
    "Puericultura": [
        "Crescimento e desenvolvimento", "Aleitamento materno e alimentação", "Imunização",
        "Prevenção de acidentes e maus-tratos",
    ],
    # Medicina Preventiva e Social
    "Atenção primária e saúde da família": [
        "Princípios da APS e Estratégia Saúde da Família", "Territorialização e diagnóstico da comunidade",
        "Visita domiciliar e abordagem familiar", "Condições crônicas na atenção primária",
        "Promoção da saúde e níveis de prevenção",
    ],
    "Epidemiologia": [
        "Indicadores de saúde e medidas de frequência", "Desenhos de estudo e medidas de associação",
        "Testes diagnósticos", "Transição demográfica e epidemiológica", "Sistemas de informação em saúde",
        "Medicina baseada em evidências", "História natural e determinantes do processo saúde-doença",
    ],
    "Ética e medicina legal": [
        "Código de ética médica e sigilo", "Documentos médicos e declaração de óbito",
        "Bioética, terminalidade e transplantes", "Tanatologia e traumatologia forense",
        "Direitos do paciente e comunicação de más notícias",
    ],
    "Políticas de saúde e SUS": [
        "Princípios e diretrizes do SUS", "Legislação e pactos do SUS", "Gestão, financiamento e controle social",
        "Redes de atenção, referência e contrarreferência", "Saúde suplementar e políticas específicas",
    ],
    "Saúde do trabalhador": [
        "Doenças relacionadas ao trabalho", "Acidente de trabalho e direitos do trabalhador",
        "Vigilância em saúde do trabalhador",
    ],
    "Vigilância em saúde": [
        "Vigilância epidemiológica e notificação compulsória", "Surtos, epidemias e investigação",
        "Vigilância sanitária e farmacovigilância", "Vigilância ambiental", "Imunização e profilaxia pós-exposição",
    ],
}

# Tipo de pergunta: o que a questão pede, pelo que as alternativas são — um
# diagnóstico (Diagnóstico); um exame, achado ou resultado (Exames); uma ação,
# como tratar, prescrever, encaminhar, orientar ou prevenir (Conduta); uma
# afirmação, mecanismo, número ou lei (Conceitos). Pedindo mais de uma coisa ("o
# diagnóstico e a conduta"), vale a etapa mais adiante: Conduta > Exames >
# Diagnóstico. Segundo eixo do desempenho, ao lado do tema.
TIPOS_PERGUNTA = ("Diagnóstico", "Exames", "Conduta", "Conceitos")

# Padrões procurados no nome normalizado (minúsculo, sem acento), do mais
# específico para o mais geral: "cirurgia vascular" precisa vencer "cirurg",
# e "ginecologia e obstetricia" precisa vencer "gineco". Especialidade None =
# o nome só identifica a grande área.
_PADROES_TAXONOMIA = [
    (r"\bginecologia e obstetricia\b", _GO, None),
    (r"\bmedicina preventiva\b|\bsaude coletiva\b", _MPS, None),
    (r"\bclinica medica\b", _CM, None),
    (r"\bcirurgia pediatrica\b", _CIR, "Cirurgia pediátrica"),
    (r"\bcirurgia vascular\b", _CIR, "Cirurgia vascular"),
    (r"\bcirurgia geral\b", _CIR, "Cirurgia geral"),
    (r"\binfectologia pediatrica\b", _PED, "Infectologia pediátrica"),
    (r"\bneonat", _PED, "Neonatologia"),
    (r"\bpuericult", _PED, "Puericultura"),
    (r"\bcardio", _CM, "Cardiologia"),
    (r"\bdermato", _CM, "Dermatologia"),
    (r"\bemergencias? clinicas?\b", _CM, "Emergências clínicas"),
    (r"\bendocrino", _CM, "Endocrinologia"),
    (r"\bgastro", _CM, "Gastroenterologia"),
    (r"\bgeriatr", _CM, "Geriatria"),
    (r"\bhemato", _CM, "Hematologia"),
    (r"\bhepato", _CM, "Hepatologia"),
    (r"\binfecto", _CM, "Infectologia"),
    (r"\bnefro", _CM, "Nefrologia"),
    (r"\bneuro(?!cirurg)", _CM, "Neurologia"),
    (r"\boncolog|\bcuidados paliativos\b", _CM, "Oncologia e cuidados paliativos"),
    (r"\bpneumo", _CM, "Pneumologia"),
    (r"\bpsiquiatr", _CM, "Psiquiatria"),
    (r"\breumato", _CM, "Reumatologia"),
    (r"\bcoloproct|\bproctolog", _CIR, "Coloproctologia"),
    (r"\boftalmo", _CIR, "Oftalmologia"),
    (r"\bortoped", _CIR, "Ortopedia"),
    (r"\botorrino", _CIR, "Otorrinolaringologia"),
    (r"\btrauma", _CIR, "Trauma"),
    (r"\burolog", _CIR, "Urologia"),
    (r"\bcirurg", _CIR, None),
    (r"\bmastolog", _GO, "Mastologia"),
    (r"\bobstetr", _GO, "Obstetrícia"),
    (r"\bgineco", _GO, "Ginecologia"),
    (r"\bpediatr", _PED, None),
    (r"\bepidemio", _MPS, "Epidemiologia"),
    (r"\bvigilancia", _MPS, "Vigilância em saúde"),
    (r"\bsaude do trabalhador\b|\bmedicina do trabalho\b", _MPS, "Saúde do trabalhador"),
    (r"\betica\b|\bmedicina legal\b", _MPS, "Ética e medicina legal"),
    (r"\batencao primaria\b|\bsaude da familia\b", _MPS, "Atenção primária e saúde da família"),
    (r"\bpoliticas? de saude\b|\bsus\b", _MPS, "Políticas de saúde e SUS"),
    (r"\bpreventiva\b", _MPS, None),
]


def normalizar_nome(texto):
    """Minúsculo, sem acento, só letras/dígitos separados por um espaço —
    'MEDCURSO - Obstetrícia_2' -> 'medcurso obstetricia 2'."""
    texto = unicodedata.normalize("NFKD", str(texto or "")).lower()
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", texto).strip()


def classificar_nome_area(nome):
    """Traduz um nome livre (coluna de planilha, por exemplo) para
    (grande área, especialidade ou None). Devolve None quando o nome não
    corresponde a nada da TAXONOMIA — quem chama decide se isso é erro."""
    texto = normalizar_nome(nome)
    if not texto:
        return None
    for area_nome, especialidades in TAXONOMIA.items():
        if texto == normalizar_nome(area_nome):
            return area_nome, None
        for esp in especialidades:
            if texto == normalizar_nome(esp):
                return area_nome, esp
    for padrao, area_nome, esp in _PADROES_TAXONOMIA:
        if re.search(padrao, texto):
            return area_nome, esp
    return None


def _ids_taxonomia(c, area_nome, especialidade_nome):
    area_id = c.execute("SELECT id FROM areas WHERE nome = ?", (area_nome,)).fetchone()["id"]
    especialidade_id = None
    if especialidade_nome:
        especialidade_id = c.execute(
            "SELECT id FROM especialidades WHERE area_id = ? AND nome = ?", (area_id, especialidade_nome)
        ).fetchone()["id"]
    return area_id, especialidade_id


def classificar_area_especialidade(nome, especialidade=None):
    """(grande área, especialidade ou None) para um nome livre de área e,
    opcional, de especialidade. `nome` pode já ser uma especialidade
    ("Cardiologia" -> Clínica Médica/Cardiologia). Uma especialidade que não
    pertence à área de `nome` é ignorada. None se `nome` não for reconhecido."""
    classe = classificar_nome_area(nome)
    if classe is None:
        return None
    area_nome, esp_nome = classe
    if especialidade:
        classe_esp = classificar_nome_area(especialidade)
        if classe_esp and classe_esp[0] == area_nome and classe_esp[1]:
            esp_nome = classe_esp[1]
    return area_nome, esp_nome


def resolver_area_especialidade(nome, especialidade=None):
    """Mesmo que classificar_area_especialidade, mas devolve os ids
    (area_id, especialidade_id)."""
    classe = classificar_area_especialidade(nome, especialidade)
    if classe is None:
        return None
    with get_conn() as conn:
        return _ids_taxonomia(conn.cursor(), *classe)


def init_db():
    """Cria as tabelas caso ainda não existam e semeia a TAXONOMIA."""
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

        # Histórico do SM-2: uma linha por avaliação (Praticar, Simulado ou
        # Revisão), só de acréscimo. `revisao` guarda apenas o estado atual e
        # cada avaliação sobrescreve a anterior — sem este log não há como
        # acompanhar a retenção do aluno ao longo do tempo. Gravado por
        # `repeticao_espacada.registrar_revisao`, na mesma transação.
        c.execute("""
        CREATE TABLE IF NOT EXISTS revisao_eventos (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER NOT NULL,
            questao_id INTEGER NOT NULL,
            origem TEXT,                  -- pratica / simulado / revisao (NULL: telas antigas do Streamlit)
            qualidade INTEGER NOT NULL,   -- nota 0–5 aplicada no SM-2
            correta INTEGER,              -- 0/1 quando houve resposta; NULL em autoavaliação
            alternativa TEXT,
            tempo_ms INTEGER,
            facilidade_antes REAL,        -- *_antes NULL na primeira avaliação da questão
            intervalo_antes INTEGER,
            repeticoes_antes INTEGER,
            atraso_dias REAL,             -- quanto já tinha vencido; negativo = revisada antes do prazo
            facilidade_depois REAL NOT NULL,
            intervalo_depois INTEGER NOT NULL,
            repeticoes_depois INTEGER NOT NULL,
            proxima_revisao TIMESTAMP NOT NULL,
            registrado_em TIMESTAMP NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
            FOREIGN KEY (questao_id) REFERENCES questoes(id) ON DELETE CASCADE
        )
        """)

        # Erros de conteúdo relatados pelos alunos. As explicações são escritas
        # do zero e a revisão de 2026-09-16 mostrou que varrer o banco inteiro
        # lendo questão por questão é caro e fraco; o relato do aluno diz onde
        # olhar. `parte` é o que ele aponta (enunciado, alternativas, gabarito,
        # Redefinição de senha: o token nunca é guardado em claro, só o seu
        # SHA-256. Quem tiver acesso de leitura ao banco não consegue usar um
        # token pendente, e o e-mail enviado é o único lugar onde ele existe.
        c.execute("""
        CREATE TABLE IF NOT EXISTS senha_tokens (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER NOT NULL,
            token_hash TEXT NOT NULL UNIQUE,
            criado_em TIMESTAMP NOT NULL,
            expira_em TIMESTAMP NOT NULL,
            usado_em TIMESTAMP,            -- NULL enquanto não foi usado
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_senha_tokens_usuario ON senha_tokens(usuario_id)")

        # explicação, imagem, outro) e é o que torna a correção dirigida.
        c.execute("""
        CREATE TABLE IF NOT EXISTS relatos_questao (
            id SERIAL PRIMARY KEY,
            questao_id INTEGER NOT NULL,
            usuario_id INTEGER NOT NULL,
            parte TEXT NOT NULL,
            comentario TEXT,
            criado_em TIMESTAMP NOT NULL,
            resolvido_em TIMESTAMP,       -- NULL enquanto pendente
            FOREIGN KEY (questao_id) REFERENCES questoes(id) ON DELETE CASCADE,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
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

        # Migração leve: edição oficial ("2025/1") e número da questão no
        # caderno, para o simulado por edição reproduzir a prova na ordem
        # original. Continuam NULL em questões sem caderno oficial identificado.
        if "edicao" not in colunas_questoes:
            c.execute("ALTER TABLE questoes ADD COLUMN edicao TEXT")
        if "numero_prova" not in colunas_questoes:
            c.execute("ALTER TABLE questoes ADD COLUMN numero_prova INTEGER")

        # Uma questão pode estar em mais de um caderno oficial: o Revalida
        # 2025/2 e o ENAMED 2025 aplicaram as mesmas questões 1–50. Esta
        # tabela é a fonte do simulado por edição; `questoes.edicao` e
        # `questoes.numero_prova` guardam só o caderno principal, porque o
        # servidor com código anterior ainda lê essas colunas.
        c.execute("SELECT to_regclass('questoes_provas') AS tabela")
        vinculos_novos = c.fetchone()["tabela"] is None
        c.execute("""
        CREATE TABLE IF NOT EXISTS questoes_provas (
            questao_id INTEGER NOT NULL,
            banca TEXT NOT NULL,
            edicao TEXT NOT NULL,
            numero_prova INTEGER NOT NULL,
            PRIMARY KEY (banca, edicao, numero_prova),
            UNIQUE (questao_id, banca, edicao),
            FOREIGN KEY (questao_id) REFERENCES questoes(id) ON DELETE CASCADE
        )
        """)
        if vinculos_novos:
            c.execute("""
                INSERT INTO questoes_provas (questao_id, banca, edicao, numero_prova)
                SELECT id, banca, edicao, numero_prova FROM questoes
                WHERE banca IS NOT NULL AND edicao IS NOT NULL AND numero_prova IS NOT NULL
            """)

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
        # Meta diária da Revisão (repeticao_espacada.plano_revisao): quantos
        # casos a tela de Revisão oferece por dia; o resto espera, por prioridade.
        if "meta_revisao_diaria" not in colunas_usuarios:
            c.execute("ALTER TABLE usuarios ADD COLUMN meta_revisao_diaria INTEGER NOT NULL DEFAULT 20")

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

        # Migração leve: edição oficial do simulado ("2025/1"); NULL no
        # simulado montado por filtros.
        c.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'simulados'
        """)
        if "edicao" not in {row["column_name"] for row in c.fetchall()}:
            c.execute("ALTER TABLE simulados ADD COLUMN edicao TEXT")

        # Tempo de tela de cada questão do simulado, somado a cada passagem por ela
        # (somar_tempo_simulado).
        c.execute("ALTER TABLE simulado_itens ADD COLUMN IF NOT EXISTS tempo_ms INTEGER")

        # Fecha o ciclo do relato: o aluno é avisado uma vez quando a questão
        # que ele apontou é corrigida. Sem isso ele relata no escuro e para de
        # relatar.
        c.execute("ALTER TABLE relatos_questao ADD COLUMN IF NOT EXISTS avisado_em TIMESTAMP")

        # Postgres não indexa colunas de FK automaticamente (só o lado
        # referenciado/PK ganha índice). Sem isso, toda query do Dashboard
        # (JOIN respostas->questoes->areas filtrando por usuario_id/banca)
        # faz sequential scan — cresce junto com o histórico de respostas.
        c.execute("CREATE INDEX IF NOT EXISTS idx_respostas_usuario_id ON respostas(usuario_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_respostas_questao_id ON respostas(questao_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_questoes_area_id ON questoes(area_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_questoes_banca ON questoes(banca)")
        # Acompanhamento de retenção: sempre por aluno, em janelas de tempo.
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_revisao_eventos_usuario_data ON revisao_eventos(usuario_id, registrado_em)"
        )
        # A tela do admin lê sempre os pendentes, mais recentes primeiro.
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_relatos_pendentes ON relatos_questao(resolvido_em, criado_em)"
        )

        conn.commit()

        # Especialidades: segundo nível da taxonomia (grande área > especialidade,
        # ver TAXONOMIA). Questões e assuntos (subtopicos) apontam
        # para a especialidade quando ela é conhecida; a área continua sendo a
        # grande área, que é o que o Painel agrega.
        c.execute("""
        CREATE TABLE IF NOT EXISTS especialidades (
            id SERIAL PRIMARY KEY,
            area_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            FOREIGN KEY (area_id) REFERENCES areas(id) ON DELETE CASCADE,
            UNIQUE(area_id, nome)
        )
        """)
        for tabela in ("questoes", "subtopicos"):
            c.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name = ?", (tabela,)
            )
            if "especialidade_id" not in {row["column_name"] for row in c.fetchall()}:
                c.execute(
                    f"ALTER TABLE {tabela} ADD COLUMN especialidade_id INTEGER "
                    "REFERENCES especialidades(id) ON DELETE SET NULL"
                )
        c.execute("CREATE INDEX IF NOT EXISTS idx_questoes_especialidade_id ON questoes(especialidade_id)")
        c.execute("ALTER TABLE questoes ADD COLUMN IF NOT EXISTS tipo_pergunta TEXT")  # TIPOS_PERGUNTA

        # Seed da taxonomia: grandes áreas, especialidades e temas. Antes
        # daqui entravam especialidades soltas como áreas ("Cardiologia",
        # "Cirurgia Geral"...), o que misturava dois níveis no mesmo filtro.
        for area_nome, especialidades in TAXONOMIA.items():
            c.execute("INSERT INTO areas (nome) VALUES (?) ON CONFLICT (nome) DO NOTHING", (area_nome,))
            area_id = c.execute("SELECT id FROM areas WHERE nome = ?", (area_nome,)).fetchone()["id"]
            for esp in especialidades:
                c.execute(
                    "INSERT INTO especialidades (area_id, nome) VALUES (?, ?) ON CONFLICT (area_id, nome) DO NOTHING",
                    (area_id, esp),
                )
        # Todos os temas numa consulta só: init_db roda a cada início da API e do
        # Streamlit, e uma ida ao Neon por tema somaria segundos.
        temas = [(area, esp, tema) for area, esps in TAXONOMIA.items() for esp in esps for tema in TEMAS[esp]]
        c.execute(f"""
            INSERT INTO subtopicos (area_id, especialidade_id, nome)
            SELECT e.area_id, e.id, t.tema
            FROM (VALUES {", ".join(["(?, ?, ?)"] * len(temas))}) AS t(area, especialidade, tema)
            JOIN areas a ON a.nome = t.area
            JOIN especialidades e ON e.area_id = a.id AND e.nome = t.especialidade
            WHERE true
            ON CONFLICT (area_id, nome) DO NOTHING
        """, [valor for linha in temas for valor in linha])
        conn.commit()


# ---------------------------------------------------------------------------
# Áreas, especialidades e temas
# ---------------------------------------------------------------------------

def listar_areas():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM areas ORDER BY nome").fetchall()


def listar_especialidades(area_id=None):
    """Especialidades (de uma grande área, ou todas) com quantas questões
    cada uma tem — as telas escondem do filtro as que estão vazias."""
    query = """
        SELECT e.id, e.area_id, e.nome,
               (SELECT COUNT(*) FROM questoes q WHERE q.especialidade_id = e.id) AS total_questoes
        FROM especialidades e
    """
    params = []
    if area_id:
        query += " WHERE e.area_id = ?"
        params.append(area_id)
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    # Ordena ignorando acento: o banco usa collation C.UTF-8, que põe "Ética"
    # depois de "Vigilância".
    return sorted(rows, key=lambda r: normalizar_nome(r["nome"]))


def listar_temas(area_id, especialidade_id=None):
    """Temas (linhas de `subtopicos` semeadas de TEMAS) da grande área, ou só
    da especialidade, com quantas questões cada um tem — o Praticar esconde os
    vazios. Os assuntos antigos da sincronização do MediaFire, que têm
    `origem`, ficam de fora."""
    query = """
        SELECT s.*, COUNT(q.id) AS total_questoes
        FROM subtopicos s
        LEFT JOIN questoes q ON q.subtopico_id = s.id
        WHERE s.area_id = ? AND s.origem IS NULL
    """
    params = [area_id]
    if especialidade_id:
        query += " AND s.especialidade_id = ?"
        params.append(especialidade_id)
    with get_conn() as conn:
        return conn.execute(query + " GROUP BY s.id ORDER BY s.nome", params).fetchall()


def obter_tema(area_id, nome):
    """Tema da grande área com esse nome, ignorando caixa e acento
    ("transtornos de ansiedade" acha "Transtornos de ansiedade"). None se não
    existir: temas são fixos, um nome importado nunca vira tema novo."""
    alvo = normalizar_nome(nome)
    return next((t for t in listar_temas(area_id) if normalizar_nome(t["nome"]) == alvo), None)


# ---------------------------------------------------------------------------
# Questões
# ---------------------------------------------------------------------------

def criar_questao(area_id, subtopico_id, enunciado, alternativas: dict,
                   resposta_correta, explicacao="", banca="", ano=None, especialidade_id=None,
                   tipo_pergunta=None):
    """Devolve o id da questão criada (a tela Nova Questão anexa a imagem nele).

    `tipo_pergunta` é um de TIPOS_PERGUNTA: sem ele a questão fica fora do filtro
    do Praticar e da seção "Por tipo de pergunta" do Painel."""
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO questoes
                (area_id, especialidade_id, subtopico_id, enunciado, alternativas, resposta_correta,
                 explicacao, banca, ano, tipo_pergunta, criada_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            area_id, especialidade_id, subtopico_id, enunciado, json.dumps(alternativas, ensure_ascii=False),
            resposta_correta, explicacao, banca, ano, tipo_pergunta,
            datetime.datetime.now().isoformat(),
        ))
        return cur.lastrowid


def atualizar_questao(questao_id, area_id, subtopico_id, enunciado, alternativas: dict,
                       resposta_correta, explicacao="", banca="", ano=None, especialidade_id=None,
                       tipo_pergunta=None):
    with get_conn() as conn:
        conn.execute("""
            UPDATE questoes
            SET area_id = ?, especialidade_id = ?, subtopico_id = ?, enunciado = ?, alternativas = ?,
                resposta_correta = ?, explicacao = ?, banca = ?, ano = ?, tipo_pergunta = ?
            WHERE id = ?
        """, (
            area_id, especialidade_id, subtopico_id, enunciado, json.dumps(alternativas, ensure_ascii=False),
            resposta_correta, explicacao, banca, ano, tipo_pergunta, questao_id,
        ))


def listar_anos():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT ano FROM questoes WHERE ano IS NOT NULL ORDER BY ano DESC"
        ).fetchall()
        return [r["ano"] for r in rows]


def ids_questoes_filtro_pratica(*, usuario_id, area_id=None, subtopico_id=None,
                                 banca=None, ano=None, apenas_erros=False,
                                 excluir_respondidas=False, especialidade_id=None, tipo_pergunta=None):
    """Configurador de Praticar (REDESIGN.md §4.2): filtros combináveis além
    de área/especialidade/subtópico — banca, ano, e dois interruptores que
    olham o histórico de respostas do próprio usuário."""
    condicoes = ["1=1"]
    params = []
    if area_id:
        condicoes.append("q.area_id = ?")
        params.append(area_id)
    if especialidade_id:
        condicoes.append("q.especialidade_id = ?")
        params.append(especialidade_id)
    if subtopico_id:
        condicoes.append("q.subtopico_id = ?")
        params.append(subtopico_id)
    if tipo_pergunta:
        condicoes.append("q.tipo_pergunta = ?")
        params.append(tipo_pergunta)
    if banca:
        # Questão aplicada em mais de uma prova oficial vale para todas as bancas.
        condicoes.append(
            "(q.banca = ? OR EXISTS (SELECT 1 FROM questoes_provas qp "
            "WHERE qp.questao_id = q.id AND qp.banca = ?))"
        )
        params.extend([banca, banca])
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
        SELECT q.*, a.nome AS area, e.nome AS especialidade, s.nome AS subtopico,
               (m.usuario_id IS NOT NULL) AS marcada
        FROM questoes q
        JOIN areas a ON a.id = q.area_id
        LEFT JOIN especialidades e ON e.id = q.especialidade_id
        LEFT JOIN subtopicos s ON s.id = q.subtopico_id
        LEFT JOIN questoes_marcadas m ON m.questao_id = q.id AND m.usuario_id = ?
        WHERE q.id IN ({placeholders})
    """
    with get_conn() as conn:
        rows = conn.execute(query, [usuario_id] + ids).fetchall()
    por_id = {r["id"]: r for r in rows}
    return [por_id[i] for i in ids if i in por_id]


def _clausulas_filtro_questoes(area_id, subtopico_id, busca, especialidade_id=None, prefixo=""):
    condicoes = ["1=1"]
    params = []
    for coluna, valor in (("area_id", area_id), ("especialidade_id", especialidade_id),
                          ("subtopico_id", subtopico_id)):
        if valor:
            condicoes.append(f"{prefixo}{coluna} = ?")
            params.append(valor)
    if busca:
        condicoes.append(f"{prefixo}enunciado ILIKE ?")
        params.append(f"%{busca}%")
    return " AND ".join(condicoes), params


def listar_questoes_paginado(area_id=None, subtopico_id=None, busca=None, limite=50, offset=0,
                             especialidade_id=None):
    condicao, params = _clausulas_filtro_questoes(area_id, subtopico_id, busca, especialidade_id, prefixo="q.")
    query = f"""
        SELECT q.*, a.nome AS area, e.nome AS especialidade
        FROM questoes q
        JOIN areas a ON a.id = q.area_id
        LEFT JOIN especialidades e ON e.id = q.especialidade_id
        WHERE {condicao} ORDER BY q.criada_em DESC LIMIT ? OFFSET ?
    """
    with get_conn() as conn:
        return conn.execute(query, params + [limite, offset]).fetchall()


def contar_questoes_filtradas(area_id=None, subtopico_id=None, busca=None, especialidade_id=None):
    condicao, params = _clausulas_filtro_questoes(area_id, subtopico_id, busca, especialidade_id)
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
    """Busca do topbar (MIGRACAO.md §5): `ILIKE` no enunciado das questões."""
    with get_conn() as conn:
        return conn.execute("""
            SELECT q.id, q.enunciado, a.nome AS area, e.nome AS especialidade
            FROM questoes q
            JOIN areas a ON a.id = q.area_id
            LEFT JOIN especialidades e ON e.id = q.especialidade_id
            WHERE q.enunciado ILIKE ? ORDER BY q.criada_em DESC LIMIT ?
        """, (f"%{termo}%", limite)).fetchall()


def contar_questoes():
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) AS n FROM questoes").fetchone()["n"]


def provas_das_questoes(ids):
    """Cadernos oficiais de cada questão ({id: [{banca, edicao, numero_prova}]}),
    da edição mais recente para a mais antiga. Uma questão pode estar em mais de
    um caderno — o Revalida 2025/2 e o ENAMED 2025 aplicaram as mesmas 43 —, e as
    colunas `questoes.banca`/`edicao` guardam só o caderno principal."""
    ids = list(ids)
    if not ids:
        return {}
    placeholders = ",".join(["?"] * len(ids))
    with get_conn() as conn:
        linhas = conn.execute(f"""
            SELECT questao_id, banca, edicao, numero_prova
            FROM questoes_provas WHERE questao_id IN ({placeholders})
            ORDER BY edicao DESC, banca
        """, ids).fetchall()
    provas = {}
    for linha in linhas:
        provas.setdefault(linha["questao_id"], []).append(
            {"banca": linha["banca"], "edicao": linha["edicao"], "numero_prova": linha["numero_prova"]}
        )
    return provas


def obter_questao(questao_id):
    with get_conn() as conn:
        return conn.execute("""
            SELECT q.*, a.nome AS area, e.nome AS especialidade, s.nome AS subtopico
            FROM questoes q
            JOIN areas a ON a.id = q.area_id
            LEFT JOIN especialidades e ON e.id = q.especialidade_id
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


def atualizar_meta_revisao(usuario_id, meta: int):
    with get_conn() as conn:
        conn.execute("UPDATE usuarios SET meta_revisao_diaria = ? WHERE id = ?", (meta, usuario_id))


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


# Partes de uma questão que o aluno pode apontar ao relatar um erro. São
# fixas de propósito: cada uma diz onde mexer, e é isso que torna a
# correção dirigida em vez de uma releitura da questão inteira.
PARTES_RELATO = ("Enunciado", "Alternativas", "Gabarito", "Explicação", "Imagem", "Outro")


def relatar_erro_questao(usuario_id, questao_id, parte, comentario=None):
    """Registra um relato de erro numa questão. `parte` precisa estar em
    PARTES_RELATO. Devolve o id do relato."""
    if parte not in PARTES_RELATO:
        raise ValueError(f"Parte inválida: {parte!r}")
    comentario = (comentario or "").strip() or None
    with get_conn() as conn:
        return conn.execute("""
            INSERT INTO relatos_questao (questao_id, usuario_id, parte, comentario, criado_em)
            VALUES (?, ?, ?, ?, ?)
            RETURNING id
        """, (questao_id, usuario_id, parte, comentario, datetime.datetime.now())).fetchone()["id"]


def listar_relatos(*, pendentes=True, limite=200):
    """Relatos com os dados da questão, mais recentes primeiro."""
    filtro = "WHERE r.resolvido_em IS NULL" if pendentes else ""
    with get_conn() as conn:
        return conn.execute(f"""
            SELECT r.id, r.questao_id, r.parte, r.comentario, r.criado_em, r.resolvido_em,
                   u.email AS usuario, q.banca, q.edicao, q.numero_prova,
                   substr(q.enunciado, 1, 90) AS trecho
            FROM relatos_questao r
            JOIN usuarios u ON u.id = r.usuario_id
            JOIN questoes q ON q.id = r.questao_id
            {filtro}
            ORDER BY r.criado_em DESC
            LIMIT ?
        """, (limite,)).fetchall()


def contar_relatos_pendentes():
    with get_conn() as conn:
        return conn.execute(
            "SELECT COUNT(*) AS n FROM relatos_questao WHERE resolvido_em IS NULL"
        ).fetchone()["n"]


def resolver_relato(relato_id):
    with get_conn() as conn:
        conn.execute(
            "UPDATE relatos_questao SET resolvido_em = ? WHERE id = ?",
            (datetime.datetime.now(), relato_id),
        )


def relatos_resolvidos_a_avisar(usuario_id):
    """Relatos deste aluno já resolvidos e que ele ainda não viu."""
    with get_conn() as conn:
        return conn.execute("""
            SELECT r.id, r.questao_id, r.parte, q.banca, q.ano, q.edicao, q.numero_prova
            FROM relatos_questao r
            JOIN questoes q ON q.id = r.questao_id
            WHERE r.usuario_id = ? AND r.resolvido_em IS NOT NULL AND r.avisado_em IS NULL
            ORDER BY r.resolvido_em
        """, (usuario_id,)).fetchall()


def marcar_relatos_avisados(usuario_id):
    """Marca como vistos os relatos resolvidos deste aluno. Por usuário, e não
    por id, para o aviso não reaparecer se dois relatos forem resolvidos entre
    a leitura e o clique."""
    with get_conn() as conn:
        conn.execute("""
            UPDATE relatos_questao SET avisado_em = ?
            WHERE usuario_id = ? AND resolvido_em IS NOT NULL AND avisado_em IS NULL
        """, (datetime.datetime.now(), usuario_id))


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
            SELECT q.*, a.nome AS area, e.nome AS especialidade
            FROM questoes_marcadas m
            JOIN questoes q ON q.id = m.questao_id
            JOIN areas a ON a.id = q.area_id
            LEFT JOIN especialidades e ON e.id = q.especialidade_id
            WHERE m.usuario_id = ?
            ORDER BY m.criada_em DESC
        """, (usuario_id,)).fetchall()


# Primeira resposta do aluno a cada questão: a base do domínio no Painel. A mesma
# questão respondida de novo mede se ele lembra dela, não se domina o assunto, e
# isso quem acompanha é a Revisão (repeticao_espacada.evolucao_memoria). `pontos`
# é o que a resposta vale no domínio: o acerto marcado como chute vale meio, porque
# o aluno não sabia (na Revisão, ele já volta mais cedo, com qualidade 3).
_PRIMEIRAS_TENTATIVAS = """
    SELECT DISTINCT ON (questao_id) id, questao_id, respondida_em,
           CASE WHEN correta = 1 AND confianca = 'chute' THEN 0.5 ELSE correta END AS pontos
    FROM respostas WHERE usuario_id = ?
    ORDER BY questao_id, id
"""


def evolucao_diaria(*, usuario_id):
    """Questões novas e % de acerto por dia (para gráfico de evolução)."""
    with get_conn() as conn:
        return conn.execute(f"""
            SELECT substr(respondida_em, 1, 10) AS dia,
                   COUNT(*) AS total,
                   SUM(pontos) AS acertos,
                   ROUND(100.0 * SUM(pontos) / COUNT(*), 1) AS pct_acerto
            FROM ({_PRIMEIRAS_TENTATIVAS}) r
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
    o Neon, uma atrás da outra). Contam só a primeira resposta a cada
    questão, com o chute valendo meio (_PRIMEIRAS_TENTATIVAS)."""
    with get_conn() as conn:
        row = conn.execute(f"""
            WITH r AS ({_PRIMEIRAS_TENTATIVAS})
            SELECT
              (SELECT jsonb_agg(t) FROM (
                  SELECT a.id AS area_id, a.nome AS area,
                         COUNT(r.id) AS total,
                         SUM(r.pontos) AS acertos,
                         ROUND(100.0 * SUM(r.pontos) / COUNT(r.id), 1) AS pct_acerto
                  FROM r
                  JOIN questoes q ON q.id = r.questao_id
                  JOIN areas a ON a.id = q.area_id
                  GROUP BY a.id, a.nome
                  ORDER BY pct_acerto ASC
              ) t) AS por_area,
              (SELECT jsonb_agg(t) FROM (
                  SELECT q.banca AS banca,
                         COUNT(r.id) AS total,
                         SUM(r.pontos) AS acertos,
                         ROUND(100.0 * SUM(r.pontos) / COUNT(r.id), 1) AS pct_acerto
                  FROM r
                  JOIN questoes q ON q.id = r.questao_id
                  WHERE q.banca IS NOT NULL AND TRIM(q.banca) != ''
                  GROUP BY q.banca
                  ORDER BY pct_acerto ASC
              ) t) AS por_banca,
              (SELECT jsonb_agg(t) FROM (
                  SELECT q.banca AS banca, a.nome AS area,
                         COUNT(r.id) AS total,
                         SUM(r.pontos) AS acertos,
                         ROUND(100.0 * SUM(r.pontos) / COUNT(r.id), 1) AS pct_acerto
                  FROM r
                  JOIN questoes q ON q.id = r.questao_id
                  JOIN areas a ON a.id = q.area_id
                  WHERE q.banca IS NOT NULL AND TRIM(q.banca) != ''
                  GROUP BY q.banca, a.nome
                  ORDER BY q.banca, a.nome
              ) t) AS por_banca_area,
              (SELECT COUNT(*)
                  FROM r
                  JOIN questoes q ON q.id = r.questao_id
                  WHERE (q.banca IS NULL OR TRIM(q.banca) = '')
              ) AS sem_banca
        """, (usuario_id,)).fetchone()
        return {
            "por_area": row["por_area"] or [],
            "por_banca": row["por_banca"] or [],
            "por_banca_area": row["por_banca_area"] or [],
            "sem_banca": row["sem_banca"] or 0,
        }


# ---------------------------------------------------------------------------
# Prioridades de estudo: onde o aluno ganha mais pontos
# ---------------------------------------------------------------------------

# Cadernos que dão o peso de cada tema na prova: os do INEP, alvo da plataforma.
BANCAS_INEP = ("REVALIDA", "ENAMED")

# Respostas "emprestadas" do nível de cima na estimativa de domínio. Com menos
# respostas próprias que isso, o tema fica mais perto da especialidade do que do
# próprio resultado. O mesmo 5 da amostra mínima do Painel.
PESO_ESTIMATIVA = 5


def estimar_dominio(acertos, total, referencia, peso=PESO_ESTIMATIVA):
    """Acerto ajustado de um grupo, de 0 a 1: começa na referência do nível de
    cima e se aproxima do resultado próprio conforme as respostas chegam."""
    return (acertos + peso * referencia) / (total + peso)


def _dominio_dos_temas(tentativas, temas):
    """(tema, domínio estimado de 0 a 1, acertos, respondidas) para cada tema,
    com as mesmas entradas de priorizar_temas. Cada nível parte do de cima:
    geral -> área -> especialidade -> tema."""
    contagem = {}  # (nível, id) -> [acertos, respondidas]
    for t in tentativas:
        for chave in (("area", t["area_id"]), ("especialidade", t["especialidade_id"]), ("tema", t["subtopico_id"])):
            grupo = contagem.setdefault(chave, [0, 0])
            grupo[0] += float(t["pontos"])
            grupo[1] += 1
    geral = sum(float(t["pontos"]) for t in tentativas) / len(tentativas)
    for tema in temas:
        dominio = geral
        for chave in (("area", tema["area_id"]), ("especialidade", tema["especialidade_id"]),
                      ("tema", tema["subtopico_id"])):
            dominio = estimar_dominio(*contagem.get(chave, (0, 0)), dominio)
        acertos, respondidas = contagem.get(("tema", tema["subtopico_id"]), (0, 0))
        yield tema, dominio, acertos, respondidas


def priorizar_temas(tentativas, temas, questoes_provas, limite=3):
    """Os `limite` temas com mais pontos a ganhar: fração da prova que o tema
    ocupa × o que falta de domínio estimado. Pura, para testar sem banco.

    tentativas: primeiras respostas (area_id, especialidade_id, subtopico_id e
        pontos: 1 no acerto, 0,5 no acerto no chute, 0 no erro).
    temas: temas que caem nos cadernos, com subtopico_id, especialidade_id,
        area_id e questoes_provas; os demais campos seguem para o resultado.
    questoes_provas: total de questões de caderno, a base da fração.
    """
    if not tentativas or not questoes_provas:
        return []
    candidatos = []
    for tema, dominio, acertos, respondidas in _dominio_dos_temas(tentativas, temas):
        fracao = tema["questoes_provas"] / questoes_provas
        candidatos.append((fracao * (1 - dominio), {
            **tema,
            "respondidas": respondidas,
            "acertos": acertos,
            "dominio_estimado": round(100 * dominio, 1),
            "peso_prova": round(100 * fracao, 1),
        }))
    candidatos.sort(key=lambda c: -c[0])
    return [dados for _, dados in candidatos[:limite]]


# Questões de uma prova do INEP (o Revalida tem 100): a variação de uma prova só
# entra na faixa da nota projetada.
QUESTOES_PROVA_INEP = 100


def projetar_nota(tentativas, temas):
    """Nota esperada numa prova do INEP, em %: o domínio estimado de cada tema
    (_dominio_dos_temas) pesado pelas questões de caderno que ele tem. A faixa
    (95%) soma a incerteza das respostas do aluno à variação de uma prova de 100
    questões, que sozinha dá uns 10 pontos para cada lado. Pura; None sem
    respostas."""
    peso_total = sum(tema["questoes_provas"] for tema in temas)
    if not tentativas or not peso_total:
        return None
    nota = sum(tema["questoes_provas"] * dominio for tema, dominio, _, _ in _dominio_dos_temas(tentativas, temas))
    nota /= peso_total
    # ponytail: margem binomial com todas as respostas; se elas se concentram em
    # poucos temas, sai um pouco estreita. Bootstrap das respostas, se importar.
    margem = 1.96 * math.sqrt(nota * (1 - nota) * (1 / len(tentativas) + 1 / QUESTOES_PROVA_INEP))
    return {
        "nota": round(100 * nota, 1),
        "minimo": round(100 * max(0.0, nota - margem), 1),
        "maximo": round(100 * min(1.0, nota + margem), 1),
        "respondidas": len(tentativas),
    }


def _tentativas_e_temas_inep(conn, usuario_id):
    """Base de prioridades_estudo e nota_projetada: as primeiras respostas do
    aluno e os temas que caem nos cadernos do INEP, com quantas questões de
    caderno cada um tem. Sem respostas, nem consulta os temas."""
    tentativas = conn.execute(f"""
        SELECT q.area_id, q.especialidade_id, q.subtopico_id, r.pontos
        FROM ({_PRIMEIRAS_TENTATIVAS}) r JOIN questoes q ON q.id = r.questao_id
    """, (usuario_id,)).fetchall()
    if not tentativas:
        return [], []
    bancas = ", ".join(["?"] * len(BANCAS_INEP))
    temas = conn.execute(f"""
        SELECT s.id AS subtopico_id, s.nome AS tema, s.especialidade_id, e.nome AS especialidade,
               s.area_id, a.nome AS area, COUNT(*) AS questoes_provas,
               COUNT(DISTINCT qp.banca || ' ' || qp.edicao) AS provas,
               (SELECT COUNT(*) FROM questoes q2 WHERE q2.subtopico_id = s.id) AS questoes_banco
        FROM questoes_provas qp
        JOIN questoes q ON q.id = qp.questao_id
        JOIN subtopicos s ON s.id = q.subtopico_id
        JOIN especialidades e ON e.id = s.especialidade_id
        JOIN areas a ON a.id = s.area_id
        WHERE qp.banca IN ({bancas})
        GROUP BY s.id, e.nome, a.nome
        ORDER BY questoes_provas DESC, s.nome
    """, BANCAS_INEP).fetchall()
    return tentativas, temas


def prioridades_estudo(*, usuario_id, limite=3):
    """Temas prioritários do aluno (priorizar_temas), com o que o Painel precisa
    para mostrar o motivo e abrir o Praticar já filtrado."""
    with get_conn() as conn:
        tentativas, temas = _tentativas_e_temas_inep(conn, usuario_id)
        if not tentativas:
            return []
        bancas = ", ".join(["?"] * len(BANCAS_INEP))
        totais = conn.execute(f"""
            SELECT COUNT(*) AS questoes, COUNT(DISTINCT banca || ' ' || edicao) AS provas
            FROM questoes_provas WHERE banca IN ({bancas})
        """, BANCAS_INEP).fetchone()
    prioridades = priorizar_temas(tentativas, temas, totais["questoes"], limite)
    return [{**p, "total_provas": totais["provas"]} for p in prioridades]


def nota_projetada(*, usuario_id):
    """Nota projetada do aluno numa prova do INEP (projetar_nota)."""
    with get_conn() as conn:
        tentativas, temas = _tentativas_e_temas_inep(conn, usuario_id)
    return projetar_nota(tentativas, temas)


def _inicio_da_semana(agora=None):
    """Segunda-feira 00:00 desta semana, o começo do ciclo do Painel."""
    dia = (agora or datetime.datetime.now()).replace(hour=0, minute=0, second=0, microsecond=0)
    return dia - datetime.timedelta(days=dia.weekday())


def progresso_semana(*, usuario_id, limite=4):
    """O antes e o depois dos temas praticados desde segunda-feira: quantas
    questões novas (primeira resposta na semana), o domínio estimado antes e
    agora e o que a Revisão cobrou do tema na semana. Fecha o ciclo do Painel:
    prioridade, prática, mudança."""
    inicio = _inicio_da_semana()
    with get_conn() as conn:
        tentativas = conn.execute(f"""
            SELECT q.area_id, q.especialidade_id, q.subtopico_id, r.pontos, r.respondida_em,
                   s.nome AS tema, e.nome AS especialidade, a.nome AS area
            FROM ({_PRIMEIRAS_TENTATIVAS}) r
            JOIN questoes q ON q.id = r.questao_id
            JOIN areas a ON a.id = q.area_id
            LEFT JOIN subtopicos s ON s.id = q.subtopico_id
            LEFT JOIN especialidades e ON e.id = q.especialidade_id
        """, (usuario_id,)).fetchall()
    # respondida_em é TEXT ISO: compara com texto.
    corte = inicio.isoformat()
    da_semana = [t for t in tentativas if t["respondida_em"] >= corte]
    antes = [t for t in tentativas if t["respondida_em"] < corte]

    praticados = {}
    for t in da_semana:
        if t["subtopico_id"] is None:
            continue
        tema = praticados.setdefault(t["subtopico_id"], {
            "subtopico_id": t["subtopico_id"], "tema": t["tema"], "area_id": t["area_id"], "area": t["area"],
            "especialidade_id": t["especialidade_id"], "especialidade": t["especialidade"],
            "novas": 0, "acertos": 0.0,
        })
        tema["novas"] += 1
        tema["acertos"] += float(t["pontos"])
    # Onde ele mais estudou primeiro; no empate, o nome, para a ordem não dançar.
    escolhidos = sorted(praticados.values(), key=lambda t: (-t["novas"], t["tema"]))[:limite]
    resumo = {
        "inicio": inicio.date().isoformat(),
        "novas": len(da_semana),
        "acertos": round(sum(float(t["pontos"]) for t in da_semana), 1),
    }
    if not escolhidos:
        return {**resumo, "temas": []}

    # Import aqui, e não no topo: repeticao_espacada importa db (ciclo).
    import repeticao_espacada
    retencao = repeticao_espacada.retencao_por_tema(usuario_id=usuario_id, desde=inicio)
    dominio_antes = {t["subtopico_id"]: d for t, d, _, _ in _dominio_dos_temas(antes, escolhidos)} if antes else {}
    dominio_agora = {t["subtopico_id"]: d for t, d, _, _ in _dominio_dos_temas(tentativas, escolhidos)}
    return {**resumo, "temas": [{
        **tema,
        "acertos": round(tema["acertos"], 1),
        "dominio_antes": round(100 * dominio_antes[tema["subtopico_id"]], 1) if antes else None,
        "dominio_agora": round(100 * dominio_agora[tema["subtopico_id"]], 1),
        **retencao.get(tema["subtopico_id"], {"testes": 0, "lembrou": 0}),
    } for tema in escolhidos]}


def desempenho_por_tipo(*, usuario_id):
    """Acerto na primeira resposta por tipo de pergunta, na ordem de
    TIPOS_PERGUNTA, incluindo os tipos ainda sem resposta (total 0)."""
    with get_conn() as conn:
        linhas = conn.execute(f"""
            SELECT q.tipo_pergunta AS tipo, COUNT(*) AS total, SUM(r.pontos) AS acertos
            FROM ({_PRIMEIRAS_TENTATIVAS}) r JOIN questoes q ON q.id = r.questao_id
            WHERE q.tipo_pergunta IS NOT NULL
            GROUP BY q.tipo_pergunta
        """, (usuario_id,)).fetchall()
    por_tipo = {linha["tipo"]: linha for linha in linhas}
    return [
        {"tipo": tipo, "total": por_tipo[tipo]["total"], "acertos": por_tipo[tipo]["acertos"]}
        if tipo in por_tipo else {"tipo": tipo, "total": 0, "acertos": 0}
        for tipo in TIPOS_PERGUNTA
    ]


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
        condicoes.append(
            "(banca = ? OR EXISTS (SELECT 1 FROM questoes_provas qp "
            "WHERE qp.questao_id = questoes.id AND qp.banca = ?))"
        )
        params.extend([banca, banca])
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


# Ritmo da prova objetiva oficial: 3 minutos por questão. Conferido em 2026-09-15
# nas bancas que existem no banco, e todas batem — Revalida, 100 questões em 5 h;
# USP/FUVEST, 120 em 6 h (instruções do caderno AD1 de 2026); UNICAMP, 80 em 4 h.
# Do ENAMED o Inep não publica a duração, e como metade das questões de 2025 é a
# mesma da Revalida 2025/2, vale o mesmo ritmo. O simulado por edição aplica isso
# às questões válidas da edição — as anuladas pelo INEP não estão no banco.
MINUTOS_POR_QUESTAO_PROVA_OFICIAL = 3


def listar_edicoes_oficiais():
    """Edições com caderno oficial identificado (`questoes_provas`), mais
    recentes primeiro, com o total de questões e o tempo de prova no ritmo
    oficial."""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT qp.banca, qp.edicao, MIN(q.ano) AS ano, COUNT(*) AS total
            FROM questoes_provas qp
            JOIN questoes q ON q.id = qp.questao_id
            GROUP BY qp.banca, qp.edicao
            ORDER BY qp.edicao DESC, qp.banca
        """).fetchall()
    return [{**r, "tempo_limite_min": r["total"] * MINUTOS_POR_QUESTAO_PROVA_OFICIAL} for r in rows]


def ids_questoes_da_edicao(banca, edicao):
    """Ids das questões de uma edição, na ordem do caderno oficial. A banca
    não diferencia maiúsculas: no banco ela está como "REVALIDA", e um
    "Revalida" digitado num script devolvia lista vazia sem erro."""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT questao_id FROM questoes_provas
            WHERE banca ILIKE ? AND edicao = ?
            ORDER BY numero_prova
        """, (banca, edicao)).fetchall()
    return [r["questao_id"] for r in rows]


def simulado_em_andamento(*, usuario_id):
    """Simulado mais recente ainda não finalizado e dentro do tempo limite,
    com quantas questões já foram respondidas. Uma prova oficial dura horas:
    o aluno pode fechar a aba e voltar. Simulado abandonado com o tempo já
    esgotado não conta como em andamento."""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT s.*,
                   (SELECT COUNT(*) FROM simulado_itens si
                    WHERE si.simulado_id = s.id AND si.resposta_dada IS NOT NULL) AS respondidas
            FROM simulados s
            WHERE s.usuario_id = ? AND s.finalizado_em IS NULL
            ORDER BY s.iniciado_em DESC
            LIMIT 5
        """, (usuario_id,)).fetchall()
    agora = datetime.datetime.now()
    for s in rows:
        inicio = datetime.datetime.fromisoformat(s["iniciado_em"])
        if inicio + datetime.timedelta(minutes=s["tempo_limite_min"]) > agora:
            return s
    return None


def criar_simulado(area_id, banca, num_questoes, tempo_limite_min, questao_ids, *, usuario_id, edicao=None):
    """Cria o registro do simulado e seus itens (na ordem de `questao_ids`:
    sorteada no simulado montado, a do caderno no simulado por edição).
    Retorna o id do simulado criado."""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO simulados
                (usuario_id, area_id, banca, edicao, num_questoes, tempo_limite_min, iniciado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (usuario_id, area_id, banca or None, edicao, num_questoes, tempo_limite_min,
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


def somar_tempo_simulado(simulado_id, questao_id, tempo_ms, *, usuario_id):
    """Soma ao item o tempo de mais uma passagem do aluno pela questão, que a
    tela manda ao sair dela. Só vale no simulado do próprio aluno e enquanto ele
    não termina: o resultado não muda depois."""
    with get_conn() as conn:
        conn.execute("""
            UPDATE simulado_itens si SET tempo_ms = COALESCE(si.tempo_ms, 0) + ?
            FROM simulados s
            WHERE s.id = si.simulado_id AND si.simulado_id = ? AND si.questao_id = ?
              AND s.usuario_id = ? AND s.finalizado_em IS NULL
        """, (tempo_ms, simulado_id, questao_id, usuario_id))


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
    Simulado (respondida/marcada/em branco), dívida resolvida na Fase 5 do
    MIGRACAO.md.

    No simulado por edição, `numero_prova` é o do caderno daquela edição: a
    mesma questão pode ter outro número em outra prova oficial."""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT si.id AS item_id, si.ordem, si.resposta_dada, si.correta, si.tempo_ms,
                   q.*, a.nome AS area, e.nome AS especialidade, sub.nome AS subtopico,
                   (m.usuario_id IS NOT NULL) AS marcada,
                   qp.numero_prova AS numero_prova_edicao
            FROM simulado_itens si
            JOIN questoes q ON q.id = si.questao_id
            JOIN areas a ON a.id = q.area_id
            LEFT JOIN especialidades e ON e.id = q.especialidade_id
            -- `sub`, e não `s`: o alias `s` é do simulado, no JOIN abaixo.
            LEFT JOIN subtopicos sub ON sub.id = q.subtopico_id
            JOIN simulados s ON s.id = si.simulado_id
            LEFT JOIN questoes_provas qp
                   ON qp.questao_id = q.id AND qp.banca = s.banca AND qp.edicao = s.edicao
            LEFT JOIN questoes_marcadas m ON m.questao_id = q.id AND m.usuario_id = ?
            WHERE si.simulado_id = ? AND s.usuario_id = ?
            ORDER BY si.ordem
        """, (usuario_id, simulado_id, usuario_id)).fetchall()
    for row in rows:
        numero_edicao = row.pop("numero_prova_edicao")
        if numero_edicao is not None:
            row["numero_prova"] = numero_edicao
    return rows


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


def temas_errados_simulado(simulado_id, *, usuario_id):
    """Temas com questão errada ou em branco no simulado, para revisar: mais
    erros primeiro e, no empate, os que mais caem nos cadernos do INEP. Área e
    especialidade vêm do tema, para o Praticar abrir já filtrado nele."""
    bancas = ", ".join(["?"] * len(BANCAS_INEP))
    with get_conn() as conn:
        return conn.execute(f"""
            SELECT t.id AS subtopico_id, t.nome AS tema, e.id AS especialidade_id, e.nome AS especialidade,
                   a.id AS area_id, a.nome AS area,
                   COUNT(*) AS total, SUM(COALESCE(si.correta, 0)) AS acertos,
                   (SELECT COUNT(*) FROM questoes q2 WHERE q2.subtopico_id = t.id) AS questoes_banco
            FROM simulado_itens si
            JOIN simulados s ON s.id = si.simulado_id
            JOIN questoes q ON q.id = si.questao_id
            JOIN subtopicos t ON t.id = q.subtopico_id
            JOIN especialidades e ON e.id = t.especialidade_id
            JOIN areas a ON a.id = t.area_id
            WHERE si.simulado_id = ? AND s.usuario_id = ?
            GROUP BY t.id, e.id, a.id
            HAVING SUM(COALESCE(si.correta, 0)) < COUNT(*)
            ORDER BY COUNT(*) - SUM(COALESCE(si.correta, 0)) DESC,
                     (SELECT COUNT(*) FROM questoes_provas qp JOIN questoes q3 ON q3.id = qp.questao_id
                      WHERE q3.subtopico_id = t.id AND qp.banca IN ({bancas})) DESC,
                     t.nome
        """, (simulado_id, usuario_id, *BANCAS_INEP)).fetchall()


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


def simulados_oficiais_feitos(*, usuario_id, limite=5):
    """Provas oficiais que o aluno terminou, da mais recente para a mais antiga.
    `ja_vistas`: questões que ele já tinha respondido antes de começar; nelas a
    nota mede memória, não preparo (o banco é feito dos próprios cadernos)."""
    with get_conn() as conn:
        return conn.execute("""
            SELECT s.id, s.banca, s.edicao, s.finalizado_em, s.num_questoes, s.acertos,
                   ROUND(100.0 * s.acertos / s.num_questoes, 1) AS pct_acerto,
                   (SELECT COUNT(*) FROM simulado_itens si
                    WHERE si.simulado_id = s.id AND EXISTS (
                        SELECT 1 FROM respostas r
                        WHERE r.usuario_id = s.usuario_id AND r.questao_id = si.questao_id
                          AND r.respondida_em < s.iniciado_em
                    )) AS ja_vistas
            FROM simulados s
            WHERE s.usuario_id = ? AND s.edicao IS NOT NULL AND s.finalizado_em IS NOT NULL
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


# --- Redefinição de senha --------------------------------------------------
# O fluxo inteiro (api/routers/auth.py) guarda só o hash do token e trata
# qualquer token inválido, expirado ou já usado do mesmo jeito: não existe.

def criar_token_senha(usuario_id, token_hash, minutos_validade=60):
    """Registra um pedido de redefinição e devolve o instante de expiração."""
    agora = datetime.datetime.now()
    expira_em = agora + datetime.timedelta(minutes=minutos_validade)
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO senha_tokens (usuario_id, token_hash, criado_em, expira_em) VALUES (?, ?, ?, ?)",
            (usuario_id, token_hash, agora, expira_em),
        )
    return expira_em


def obter_token_senha(token_hash):
    """Token utilizável: existe, não foi usado e não expirou. Qualquer outro
    caso devolve None, para o chamador não poder distinguir os motivos."""
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT * FROM senha_tokens
            WHERE token_hash = ? AND usado_em IS NULL AND expira_em > ?
            """,
            (token_hash, datetime.datetime.now()),
        ).fetchone()


def contar_tokens_recentes(usuario_id, minutos=15):
    """Quantos pedidos a conta fez na última janela — o freio contra usar o
    'esqueci minha senha' para bombardear a caixa de entrada de alguém."""
    desde = datetime.datetime.now() - datetime.timedelta(minutes=minutos)
    with get_conn() as conn:
        row = conn.execute(
            "SELECT count(*) AS n FROM senha_tokens WHERE usuario_id = ? AND criado_em > ?",
            (usuario_id, desde),
        ).fetchone()
    return row["n"]


def redefinir_senha(usuario_id, senha_hash, token_id):
    """Troca a senha e queima **todos** os tokens da conta na mesma transação:
    usar um link não pode deixar os outros pendentes valendo."""
    agora = datetime.datetime.now()
    with get_conn() as conn:
        conn.execute("UPDATE usuarios SET senha_hash = ? WHERE id = ?", (senha_hash, usuario_id))
        conn.execute(
            "UPDATE senha_tokens SET usado_em = ? WHERE usuario_id = ? AND usado_em IS NULL",
            (agora, usuario_id),
        )
        return token_id
