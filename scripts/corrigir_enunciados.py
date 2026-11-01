"""Corrige enunciados a partir de um JSON {id: texto novo}, conferido contra o caderno.

Simula por padrão; grava só com --aplicar, numa transação, guardando o texto
anterior em backups/. Antes do --aplicar: `python scripts/backup_banco.py`.

Lista os números que entram e que saem de cada enunciado: tirar um dado clínico por
engano é o erro que importa aqui, e a lista o mostra sem precisar reler tudo.

    python scripts/corrigir_enunciados.py backups/correcoes_enunciados.json
    python scripts/corrigir_enunciados.py backups/correcoes_enunciados.json --aplicar
"""

import argparse
import collections
import json
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db

BACKUPS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups")


def diferenca_de_numeros(antes, depois):
    """(só no antigo, só no novo), contando repetições."""
    a = collections.Counter(re.findall(r"\d+(?:[.,]\d+)*", antes))
    b = collections.Counter(re.findall(r"\d+(?:[.,]\d+)*", depois))
    return sorted((a - b).elements()), sorted((b - a).elements())


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("json", help='arquivo {"<id>": "novo enunciado", ...}')
    p.add_argument("--aplicar", action="store_true")
    args = p.parse_args()

    with open(args.json, encoding="utf-8") as f:
        novas = json.load(f)

    anteriores = {}
    with db.get_conn() as con:
        for qid, texto in novas.items():
            q = db.obter_questao(int(qid))
            if q is None:
                p.error("questão %s não existe" % qid)
            if not texto.strip():
                p.error("enunciado vazio para a questão %s" % qid)
            anteriores[qid] = q["enunciado"]
            saem, entram = diferenca_de_numeros(q["enunciado"], texto)
            print("Questão %s — %s %s, questão %s do caderno" % (qid, q["banca"], q["edicao"], q["numero_prova"]))
            print("  antes %d caracteres, agora %d" % (len(q["enunciado"]), len(texto)))
            print("  números que saem: %s" % (saem or "nenhum"))
            print("  números que entram: %s" % (entram or "nenhum"))

        if not args.aplicar:
            print("\n%d enunciado(s). Simulação — nada gravado. Use --aplicar." % len(novas))
            return

        os.makedirs(BACKUPS, exist_ok=True)
        destino = os.path.join(BACKUPS, "enunciados_%s.json" % datetime.now().strftime("%Y%m%d_%H%M%S"))
        with open(destino, "w", encoding="utf-8") as f:
            json.dump(anteriores, f, ensure_ascii=False, indent=1)
        print("\nbackup do texto anterior: %s" % destino)

        for qid, texto in novas.items():
            con.execute("UPDATE questoes SET enunciado = ? WHERE id = ?", (texto, int(qid)))
        print("%d enunciado(s) gravado(s)." % len(novas))


if __name__ == "__main__":
    main()
