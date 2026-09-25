"""
A paleta do avatar e das pastas (frontend/src/lib/paleta.json). O mesmo JSON
serve o front, que desenha, e o banco, que valida; este teste prende o que os
dois dependem que seja verdade, sem tocar no banco.
"""

import db


def _luminancia(hexa):
    canais = [int(hexa[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = (c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in canais)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contraste(a, b):
    claro, escuro = sorted((_luminancia(a), _luminancia(b)), reverse=True)
    return (claro + 0.05) / (escuro + 0.05)


def test_todo_tom_tem_texto_legivel_por_cima():
    # O título da pasta é 17px/700, que não conta como texto grande: vale 4,5:1.
    assert len(db.PALETA["familias"]) == 10
    for familia in db.PALETA["familias"]:
        assert len(familia["tons"]) == 8, familia["chave"]
        for tom in familia["tons"]:
            assert _contraste(tom["hex"], tom["on"]) >= 4.5, (familia["chave"], tom)


def test_chave_antiga_vira_tom_novo_e_o_resto_cai_no_padrao():
    assert db.normalizar_cor("azul-3", "pasta") == "azul-3"
    # A ameixa apagada do avatar vai para o roxo, e não para o cinza, que era o
    # vizinho mais próximo pela distância pura (HISTORICO.md, 2026-09-24).
    assert db.normalizar_cor("ameixa", "perfil") == "roxo-7"
    assert db.normalizar_cor("ardosia", "pasta") == db.COR_PASTA_PADRAO
    for lixo in ("azul-9", "azul", "", None, "red; background: url(x)"):
        assert db.normalizar_cor(lixo, "perfil") == db.COR_PERFIL_PADRAO
    for tabela in db.PALETA["legado"].values():
        assert set(tabela.values()) <= db.CORES
    assert {db.COR_PERFIL_PADRAO, db.COR_PASTA_PADRAO} <= db.CORES
