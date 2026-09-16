"""
Helpers de serialização compartilhados entre routers. Existem porque
`questoes.imagem` é BYTEA (bytes/memoryview) — o FastAPI não sabe
serializar isso em JSON, e nenhuma tela deveria embutir a imagem inteira
dentro do payload da questão de qualquer forma (ela é grande e tem seu
próprio endpoint, `GET /questoes/{id}/imagem`). Toda rota que devolve uma
linha de `questoes` (direto ou via JOIN) deve passar por aqui.
"""

import json

import db


def questao_publica(row: dict, provas=None) -> dict:
    d = dict(row)
    tem_imagem = d.pop("imagem", None) is not None
    d.pop("imagem_mime", None)
    d["tem_imagem"] = tem_imagem
    # `questoes.alternativas` é TEXT no Postgres (json.dumps na escrita,
    # em db.py) — sem isso o cliente recebe uma string JSON dentro do JSON
    # da resposta e precisaria fazer um segundo JSON.parse manual.
    if isinstance(d.get("alternativas"), str):
        d["alternativas"] = json.loads(d["alternativas"])
    if provas is not None:
        d["provas"] = provas.get(d.get("id"), [])
    return d


def questoes_publicas(rows) -> list:
    """Serializa um lote e anexa a `provas` de cada questão (db.provas_das_questoes)
    numa consulta só. `questoes.banca`/`edicao` trazem apenas o caderno principal,
    então é daqui que as telas sabem que a mesma questão caiu em duas provas."""
    rows = list(rows)
    provas = db.provas_das_questoes([r["id"] for r in rows if r.get("id") is not None])
    return [questao_publica(row, provas) for row in rows]
