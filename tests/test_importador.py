"""
Importação de questoes: o tipo de pergunta é obrigatório, porque questão sem
tipo fica fora do filtro do Praticar e da seção "Por tipo de pergunta" do
Painel (`db.TIPOS_PERGUNTA`).
"""

import json
import uuid

import pandas as pd

import db
import importador_questoes as imp


def _linha(**extra):
    linha = {
        "area": "Cardiologia",
        "enunciado": f"[pytest {uuid.uuid4().hex[:8]}] Enunciado de teste.",
        "alternativa_a": "a", "alternativa_b": "b", "alternativa_c": "c", "alternativa_d": "d",
        "resposta_correta": "A",
        "tipo_pergunta": "Conduta",
    }
    linha.update(extra)
    return linha


def test_planilha_sem_coluna_de_tipo_e_recusada():
    df = pd.DataFrame([_linha()]).drop(columns=["tipo_pergunta"])
    assert "tipo_pergunta" in imp.validar_planilha(df)


def test_linha_sem_tipo_ou_com_tipo_desconhecido_nao_e_importada():
    # Nada é gravado: a checagem do tipo vem antes de resolver a área e do INSERT.
    df = pd.DataFrame([_linha(tipo_pergunta=""), _linha(tipo_pergunta="Prognostico")])
    relatorio = imp.importar(df)
    assert relatorio["importadas"] == 0
    assert [n for n, _ in relatorio["erros"]] == [2, 3]
    assert all("tipo inválido" in motivo for _, motivo in relatorio["erros"])


def test_criar_questao_grava_o_tipo(area_teste):
    questao_id = db.criar_questao(
        area_teste, None, f"[pytest {uuid.uuid4().hex[:8]}] Questao de teste.",
        {"A": "certa", "B": "errada"}, "A", banca="PYTEST", ano=2024,
        tipo_pergunta="Exames",
    )
    try:
        assert db.obter_questao(questao_id)["tipo_pergunta"] == "Exames"
        db.atualizar_questao(
            questao_id, area_teste, None, "reescrito", {"A": "certa", "B": "errada"}, "A",
            banca="PYTEST", ano=2024, tipo_pergunta="Conduta",
        )
        assert db.obter_questao(questao_id)["tipo_pergunta"] == "Conduta"
    finally:
        with db.get_conn() as conn:
            conn.execute("DELETE FROM questoes WHERE id = ?", (questao_id,))


def test_json_das_alternativas_continua_intacto(area_teste):
    # criar_questao ganhou uma coluna nova; o JSON não pode ter deslizado de posição.
    alternativas = {"A": "certa", "B": "errada", "C": "outra"}
    questao_id = db.criar_questao(
        area_teste, None, f"[pytest {uuid.uuid4().hex[:8]}] Questao de teste.",
        alternativas, "A", tipo_pergunta="Conceitos",
    )
    try:
        assert json.loads(db.obter_questao(questao_id)["alternativas"]) == alternativas
    finally:
        with db.get_conn() as conn:
            conn.execute("DELETE FROM questoes WHERE id = ?", (questao_id,))
