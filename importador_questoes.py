"""
Importação em massa de questões a partir de uma planilha (.xlsx ou .csv).

Formato esperado (nomes de coluna flexíveis — veja `COLUNAS_ACEITAS`):

area | especialidade | tema | enunciado | alternativa_a | alternativa_b
| alternativa_c | alternativa_d | alternativa_e | resposta_correta | tipo | explicacao
| banca | ano

- `area` é obrigatória e segue a taxonomia fixa (`db.TAXONOMIA`): pode ser a
  grande área ("Clínica Médica") ou já a especialidade ("Cardiologia"). Um
  nome que não corresponde a nada vira erro da linha — nunca uma área nova.
- `especialidade` e `tema` são opcionais. O tema segue a mesma regra: precisa
  ser um dos temas fixos da área (`db.TEMAS`), senão a linha vira erro.
- `tipo` é o tipo de pergunta (`db.TIPOS_PERGUNTA`), pelo que as alternativas
  pedem, e é obrigatório: sem ele a questão fica fora do filtro do Praticar e
  da seção "Por tipo de pergunta" do Painel.
- `alternativa_e` é opcional (questões com 4 ou 5 alternativas).
- `resposta_correta` deve ser a letra (A, B, C, D ou E).
"""

import io
import pandas as pd

import db

# Aceita variações comuns de nome de coluna / acentuação, para não travar
# a importação por causa de um cabeçalho digitado diferente.
COLUNAS_ACEITAS = {
    "area": "area",
    "área": "area",
    "especialidade": "especialidade",
    "tema": "subtopico",
    "subtopico": "subtopico",
    "subtópico": "subtopico",
    "assunto": "subtopico",
    "enunciado": "enunciado",
    "pergunta": "enunciado",
    "alternativa_a": "alternativa_a",
    "a": "alternativa_a",
    "alternativa_b": "alternativa_b",
    "b": "alternativa_b",
    "alternativa_c": "alternativa_c",
    "c": "alternativa_c",
    "alternativa_d": "alternativa_d",
    "d": "alternativa_d",
    "alternativa_e": "alternativa_e",
    "e": "alternativa_e",
    "tipo": "tipo_pergunta",
    "tipo_pergunta": "tipo_pergunta",
    "tipo_de_pergunta": "tipo_pergunta",
    "resposta_correta": "resposta_correta",
    "gabarito": "resposta_correta",
    "resposta": "resposta_correta",
    "explicacao": "explicacao",
    "explicação": "explicacao",
    "comentario": "explicacao",
    "comentário": "explicacao",
    "banca": "banca",
    "instituicao": "banca",
    "instituição": "banca",
    "ano": "ano",
}

COLUNAS_OBRIGATORIAS = [
    "area", "enunciado", "alternativa_a", "alternativa_b",
    "alternativa_c", "alternativa_d", "resposta_correta", "tipo_pergunta",
]


def _normalizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    novas_colunas = {}
    for col in df.columns:
        chave = str(col).strip().lower().replace(" ", "_")
        novas_colunas[col] = COLUNAS_ACEITAS.get(chave, chave)
    return df.rename(columns=novas_colunas)


def ler_planilha(arquivo, nome_arquivo: str) -> pd.DataFrame:
    """`arquivo` pode ser um caminho ou um objeto tipo arquivo (ex: o que
    vem do st.file_uploader do Streamlit)."""
    if nome_arquivo.lower().endswith(".csv"):
        df = pd.read_csv(arquivo, dtype=str, keep_default_na=False)
    else:
        df = pd.read_excel(arquivo, dtype=str)
        df = df.fillna("")
    return _normalizar_colunas(df)


def validar_planilha(df: pd.DataFrame):
    """Retorna lista de colunas obrigatórias que estão faltando."""
    faltando = [c for c in COLUNAS_OBRIGATORIAS if c not in df.columns]
    return faltando


def importar(df: pd.DataFrame):
    """
    Importa todas as linhas válidas da planilha para o banco.

    Retorna um relatório:
        {
            "total": int,
            "importadas": int,
            "duplicadas": int,
            "erros": [ (numero_da_linha, motivo), ... ],
        }
    """
    relatorio = {"total": len(df), "importadas": 0, "duplicadas": 0, "erros": []}

    for i, row in df.iterrows():
        linha_num = i + 2  # +2 = cabeçalho (linha 1) + índice 0-based

        area_nome = str(row.get("area", "")).strip()
        enunciado = str(row.get("enunciado", "")).strip()
        alt_a = str(row.get("alternativa_a", "")).strip()
        alt_b = str(row.get("alternativa_b", "")).strip()
        alt_c = str(row.get("alternativa_c", "")).strip()
        alt_d = str(row.get("alternativa_d", "")).strip()
        alt_e = str(row.get("alternativa_e", "")).strip()
        resposta_correta = str(row.get("resposta_correta", "")).strip().upper()
        explicacao = str(row.get("explicacao", "")).strip()
        banca = str(row.get("banca", "")).strip()
        especialidade_nome = str(row.get("especialidade", "")).strip()
        subtopico_nome = str(row.get("subtopico", "")).strip()
        tipo_pergunta = str(row.get("tipo_pergunta", "")).strip()
        ano_raw = str(row.get("ano", "")).strip()

        if not area_nome:
            relatorio["erros"].append((linha_num, "Área em branco"))
            continue
        if not enunciado:
            relatorio["erros"].append((linha_num, "Enunciado em branco"))
            continue
        if not all([alt_a, alt_b, alt_c, alt_d]):
            relatorio["erros"].append((linha_num, "Faltam alternativas A a D"))
            continue

        alternativas = {"A": alt_a, "B": alt_b, "C": alt_c, "D": alt_d}
        if alt_e:
            alternativas["E"] = alt_e

        if resposta_correta not in alternativas:
            relatorio["erros"].append(
                (linha_num, f"resposta_correta inválida: '{resposta_correta}' (use A-{'E' if alt_e else 'D'})")
            )
            continue

        if tipo_pergunta not in db.TIPOS_PERGUNTA:
            relatorio["erros"].append(
                (linha_num, "tipo inválido: '%s' (use %s)" % (tipo_pergunta, ", ".join(db.TIPOS_PERGUNTA)))
            )
            continue

        try:
            ano = int(float(ano_raw)) if ano_raw else None
        except ValueError:
            ano = None

        ids = db.resolver_area_especialidade(area_nome, especialidade=especialidade_nome or None)
        if ids is None:
            relatorio["erros"].append(
                (linha_num, f"Área '{area_nome}' não corresponde a nenhuma grande área ou especialidade")
            )
            continue
        area_id, especialidade_id = ids
        subtopico_id = None
        if subtopico_nome:
            tema = db.obter_tema(area_id, subtopico_nome)
            if tema is None:
                relatorio["erros"].append((linha_num, f"Tema '{subtopico_nome}' não é um dos temas da área"))
                continue
            subtopico_id = tema["id"]
            especialidade_id = especialidade_id or tema["especialidade_id"]

        if db.questao_ja_existe(area_id, enunciado):
            relatorio["duplicadas"] += 1
            continue

        db.criar_questao(
            area_id, subtopico_id, enunciado, alternativas,
            resposta_correta, explicacao, banca, ano, especialidade_id=especialidade_id,
            tipo_pergunta=tipo_pergunta,
        )
        relatorio["importadas"] += 1

    return relatorio


def gerar_template_bytes() -> bytes:
    """Gera um .xlsx modelo (com um exemplo preenchido) para o usuário
    baixar, preencher e reimportar."""
    df = pd.DataFrame([{
        "area": "Clínica Médica",
        "especialidade": "Cardiologia",
        "tema": "Arritmias",
        "enunciado": "Paciente com fibrilação atrial de início há 6 horas, hemodinamicamente "
                      "instável. Qual a conduta imediata?",
        "alternativa_a": "Cardioversão elétrica imediata",
        "alternativa_b": "Anticoagulação plena e reavaliação em 48h",
        "alternativa_c": "Betabloqueador oral e alta",
        "alternativa_d": "Observação clínica sem intervenção",
        "alternativa_e": "",
        "resposta_correta": "A",
        "tipo": "Conduta",
        "explicacao": "Instabilidade hemodinâmica é indicação de cardioversão elétrica imediata, "
                       "independentemente do tempo de anticoagulação.",
        "banca": "ENAMED",
        "ano": 2024,
    }])
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="questoes")
    return buffer.getvalue()
