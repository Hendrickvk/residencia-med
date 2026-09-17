"""Despeja as questões de uma edição em texto, para leitura e revisão.

    python scripts/dump_explicacoes.py USP 2026 --de 1 --ate 15
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db


def main():
    # O console do Windows usa cp1252 e quebra em caracteres como o sinal de
    # menos tipográfico (U+2212) que vem da extração dos PDFs.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("banca")
    p.add_argument("edicao")
    p.add_argument("--de", type=int, default=1, help="primeira questão do caderno")
    p.add_argument("--ate", type=int, default=10**6, help="última questão do caderno")
    args = p.parse_args()

    for qid in db.ids_questoes_da_edicao(args.banca, args.edicao):
        q = db.obter_questao(qid)
        n = q["numero_prova"]
        if not (args.de <= n <= args.ate):
            continue
        print("=" * 70)
        print("Q%s do caderno | id %s | %s > %s > %s | %s%s" % (
            n, q["id"], q["area"], q["especialidade"], q["subtopico"],
            q["tipo_pergunta"], " | TEM IMAGEM" if q["imagem"] else ""))
        print(q["enunciado"])
        for letra, texto in db.json.loads(q["alternativas"]).items():
            marca = " <<< GABARITO" if letra == q["resposta_correta"] else ""
            print("  %s) %s%s" % (letra, texto, marca))
        print("--- explicação:")
        print(q["explicacao"] or "(sem explicação)")
        print()


if __name__ == "__main__":
    main()
