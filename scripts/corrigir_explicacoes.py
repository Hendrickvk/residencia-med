"""Reescreve explicações de questões a partir de um JSON {id: texto novo}.

Simula por padrão; grava só com --aplicar, numa transação, guardando o texto
anterior em backups/.

    python scripts/corrigir_explicacoes.py backups/explicacoes_usp2026.json
    python scripts/corrigir_explicacoes.py backups/explicacoes_usp2026.json --aplicar
"""

import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db

BACKUPS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("json", help='arquivo {"<id>": "nova explicação", ...}')
    p.add_argument("--aplicar", action="store_true")
    args = p.parse_args()

    with open(args.json, encoding="utf-8") as f:
        novas = json.load(f)

    anteriores = {}
    with db.get_conn() as con:
        cur = con.cursor()
        for qid, texto in novas.items():
            q = db.obter_questao(int(qid))
            if q is None:
                p.error("questão %s não existe" % qid)
            if not texto.strip():
                p.error("explicação vazia para a questão %s" % qid)
            anteriores[qid] = q["explicacao"]
            print("Questão %s — %s %s, questão %s do caderno" % (
                qid, q["banca"], q["edicao"], q["numero_prova"]))
            print("  gabarito %s | antes %d caracteres, agora %d" % (
                q["resposta_correta"], len(q["explicacao"] or ""), len(texto)))
            # Checagem barata: a explicação tem de citar o texto da alternativa
            # correta. Não substitui leitura, mas pega o caso de escrever a
            # explicação para a letra errada. Nas questões de alternativa-imagem
            # o enunciado da alternativa é só "Imagem B.", sem conteúdo com que
            # comparar — ali a checagem não diz nada e é pulada.
            alt = db.json.loads(q["alternativas"])[q["resposta_correta"]]
            if alt.strip().lower().rstrip(".").startswith("imagem "):
                continue
            marcas = [w for w in alt.lower().replace(".", "").split() if len(w) > 5]
            if marcas and not any(w in texto.lower() for w in marcas):
                print("  ATENÇÃO: o texto não cita nenhuma palavra da alternativa correta.")

        if not args.aplicar:
            print("\n%d explicação(ões). Simulação — nada gravado. Use --aplicar." % len(novas))
            return

        os.makedirs(BACKUPS, exist_ok=True)
        destino = os.path.join(
            BACKUPS, "explicacoes_%s.json" % datetime.now().strftime("%Y%m%d_%H%M%S"))
        with open(destino, "w", encoding="utf-8") as f:
            json.dump(anteriores, f, ensure_ascii=False, indent=1)
        print("\nbackup do texto anterior: %s" % destino)

        for qid, texto in novas.items():
            cur.execute("UPDATE questoes SET explicacao = %s WHERE id = %s", (texto, int(qid)))
        con.commit()
        print("%d explicação(ões) gravada(s)." % len(novas))


if __name__ == "__main__":
    main()
