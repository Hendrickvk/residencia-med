"""
Helpers de serialização compartilhados entre routers. Existem porque
`questoes.imagem` é BYTEA (bytes/memoryview) — o FastAPI não sabe
serializar isso em JSON, e nenhuma tela deveria embutir a imagem inteira
dentro do payload da questão de qualquer forma (ela é grande e tem seu
próprio endpoint, `GET /questoes/{id}/imagem`). Toda rota que devolve uma
linha de `questoes` (direto ou via JOIN) deve passar por aqui.
"""

import json


def questao_publica(row: dict) -> dict:
    d = dict(row)
    tem_imagem = d.pop("imagem", None) is not None
    d.pop("imagem_mime", None)
    d["tem_imagem"] = tem_imagem
    # `questoes.alternativas` é TEXT no Postgres (json.dumps na escrita,
    # em db.py) — sem isso o cliente recebe uma string JSON dentro do JSON
    # da resposta e precisaria fazer um segundo JSON.parse manual.
    if isinstance(d.get("alternativas"), str):
        d["alternativas"] = json.loads(d["alternativas"])
    return d
