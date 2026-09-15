"""
Taxonomia grande área > especialidade > tema (`db.TAXONOMIA`, `db.TEMAS`): o
resolvedor de nomes livres usado pelo importador de planilha e os filtros por
especialidade e por tema do Praticar.
"""

import pytest

import db


def test_toda_area_e_especialidade_resolve_para_ela_mesma():
    for area, especialidades in db.TAXONOMIA.items():
        assert db.classificar_nome_area(area) == (area, None)
        for esp in especialidades:
            assert db.classificar_nome_area(esp) == (area, esp)


@pytest.mark.parametrize("nome, esperado", [
    ("Aprenda Nefro - Gasometria - Curso Completo", ("Clínica Médica", "Nefrologia")),
    ("CardioPapers ECG", ("Clínica Médica", "Cardiologia")),
    ("MEDCURSO - PSIQUIATRIA", ("Clínica Médica", "Psiquiatria")),
    ("Gastrologia", ("Clínica Médica", "Gastroenterologia")),
    ("Cirurgia Geral", ("Cirurgia", "Cirurgia geral")),
    ("GINECOLOGIA E OBSTETRÍCIA", ("Ginecologia e Obstetrícia", None)),
    ("Preventiva", ("Medicina Preventiva e Social", None)),
    ("Material diverso", None),
])
def test_classificar_nome_area(nome, esperado):
    assert db.classificar_nome_area(nome) == esperado


def test_especialidade_de_outra_area_e_ignorada():
    assert db.classificar_area_especialidade("Pediatria", "Cardiologia") == ("Pediatria", None)
    assert db.classificar_area_especialidade("Pediatria", "Neonatologia") == ("Pediatria", "Neonatologia")


def test_temas_cobrem_toda_especialidade_sem_repetir_na_area():
    especialidades = {esp for lista in db.TAXONOMIA.values() for esp in lista}
    assert set(db.TEMAS) == especialidades
    for area, lista in db.TAXONOMIA.items():
        nomes = [tema for esp in lista for tema in db.TEMAS[esp]]
        # subtopicos é UNIQUE(area_id, nome): dois temas iguais na mesma grande área colidiriam.
        assert len(nomes) == len(set(nomes)), area


@pytest.fixture(scope="module")
def temas_semeados():
    db.init_db()


def test_init_db_semeia_os_temas_ligados_a_especialidade(temas_semeados):
    with db.get_conn() as conn:
        linhas = conn.execute("""
            SELECT a.nome AS area, e.nome AS especialidade, s.nome AS tema
            FROM subtopicos s
            JOIN areas a ON a.id = s.area_id
            JOIN especialidades e ON e.id = s.especialidade_id
            WHERE s.origem IS NULL
        """).fetchall()
    semeados = {(l["area"], l["especialidade"], l["tema"]) for l in linhas}
    esperados = {(a, e, t) for a, esps in db.TAXONOMIA.items() for e in esps for t in db.TEMAS[e]}
    assert esperados <= semeados


def test_obter_tema_ignora_caixa_e_acento_e_nao_inventa_tema(temas_semeados):
    area_id = next(a["id"] for a in db.listar_areas() if a["nome"] == "Clínica Médica")
    tema = db.obter_tema(area_id, "  TRANSTORNOS DE ANSIEDADE ")
    assert tema["nome"] == "Transtornos de ansiedade"
    assert db.obter_tema(area_id, "Assunto inventado") is None
    # Temas de outra grande área não valem nesta.
    assert db.obter_tema(area_id, "Climatério") is None


@pytest.fixture()
def especialidades_teste(area_teste):
    ids = []
    with db.get_conn() as conn:
        for nome in ("__pytest_esp_a", "__pytest_esp_b"):
            conn.execute("INSERT INTO especialidades (area_id, nome) VALUES (?, ?)", (area_teste, nome))
            ids.append(conn.execute(
                "SELECT id FROM especialidades WHERE area_id = ? AND nome = ?", (area_teste, nome)
            ).fetchone()["id"])
    yield ids
    with db.get_conn() as conn:
        for esp_id in ids:
            conn.execute("DELETE FROM especialidades WHERE id = ?", (esp_id,))


def test_filtro_por_especialidade_em_praticar(usuario_teste, area_teste, questao_teste, especialidades_teste):
    esp_a, esp_b = especialidades_teste
    with db.get_conn() as conn:
        conn.execute("UPDATE questoes SET especialidade_id = ? WHERE id = ?", (esp_a, questao_teste))

    assert questao_teste in db.ids_questoes_filtro_pratica(usuario_id=usuario_teste, especialidade_id=esp_a)
    assert questao_teste not in db.ids_questoes_filtro_pratica(usuario_id=usuario_teste, especialidade_id=esp_b)
    [questao] = db.obter_questoes_por_ids([questao_teste], usuario_id=usuario_teste)
    assert questao["especialidade"] == "__pytest_esp_a"

    contagens = {e["nome"]: e["total_questoes"] for e in db.listar_especialidades(area_teste)}
    assert contagens == {"__pytest_esp_a": 1, "__pytest_esp_b": 0}


def test_filtro_por_tema_em_praticar(usuario_teste, area_teste, questao_teste, especialidades_teste):
    esp_a, _ = especialidades_teste
    temas = []
    # Os temas somem com a área de teste (subtopicos.area_id é ON DELETE CASCADE).
    with db.get_conn() as conn:
        for nome in ("__pytest_tema_a", "__pytest_tema_b"):
            conn.execute(
                "INSERT INTO subtopicos (area_id, especialidade_id, nome) VALUES (?, ?, ?)", (area_teste, esp_a, nome)
            )
            temas.append(conn.execute(
                "SELECT id FROM subtopicos WHERE area_id = ? AND nome = ?", (area_teste, nome)
            ).fetchone()["id"])
        conn.execute(
            "UPDATE questoes SET especialidade_id = ?, subtopico_id = ? WHERE id = ?", (esp_a, temas[0], questao_teste)
        )

    assert questao_teste in db.ids_questoes_filtro_pratica(usuario_id=usuario_teste, subtopico_id=temas[0])
    assert questao_teste not in db.ids_questoes_filtro_pratica(usuario_id=usuario_teste, subtopico_id=temas[1])
    [questao] = db.obter_questoes_por_ids([questao_teste], usuario_id=usuario_teste)
    assert questao["subtopico"] == "__pytest_tema_a"

    contagens = {t["nome"]: t["total_questoes"] for t in db.listar_temas(area_teste, esp_a)}
    assert contagens == {"__pytest_tema_a": 1, "__pytest_tema_b": 0}
