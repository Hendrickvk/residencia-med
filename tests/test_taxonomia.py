"""
Taxonomia grande área > especialidade (`db.TAXONOMIA`): o resolvedor de
nomes livres usado pelo importador de planilha e o filtro por especialidade
do Praticar.
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
