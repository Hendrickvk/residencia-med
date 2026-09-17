"""Troca a imagem de uma questão, guardando a anterior em backups/.

Simula por padrão; grava só com --aplicar.

    python scripts/substituir_imagem.py 3232 recorte.png
    python scripts/substituir_imagem.py 3232 recorte.png --aplicar
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db

BACKUPS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("questao_id", type=int)
    p.add_argument("imagem", help="arquivo PNG/JPEG com o novo recorte")
    p.add_argument("--aplicar", action="store_true", help="grava de verdade")
    args = p.parse_args()

    with open(args.imagem, "rb") as f:
        nova = f.read()
    mime = mimetypes.guess_type(args.imagem)[0]
    if mime not in ("image/png", "image/jpeg"):
        p.error("a imagem precisa ser PNG ou JPEG (veio %s)" % mime)

    with db.get_conn() as con:
        cur = con.cursor()
        cur.execute(
            "SELECT id, enunciado, banca, edicao, numero_prova, imagem, imagem_mime"
            " FROM questoes WHERE id = %s",
            (args.questao_id,),
        )
        q = cur.fetchone()
        if not q:
            p.error("questão %d não existe" % args.questao_id)

        antiga = bytes(q["imagem"]) if q["imagem"] else None
        print("Questão %d — %s %s, questão %s do caderno" % (
            q["id"], q["banca"], q["edicao"], q["numero_prova"]))
        print("  %s" % q["enunciado"][:90].replace("\n", " "))
        print("  imagem atual: %s, %d bytes" % (q["imagem_mime"], len(antiga) if antiga else 0))
        print("  imagem nova : %s, %d bytes (%s)" % (mime, len(nova), args.imagem))

        if not args.aplicar:
            print("\nSimulação — nada gravado. Use --aplicar.")
            return

        os.makedirs(BACKUPS, exist_ok=True)
        destino = os.path.join(
            BACKUPS, "imagem_q%d_%s.json" % (q["id"], datetime.now().strftime("%Y%m%d_%H%M%S")))
        with open(destino, "w", encoding="utf-8") as f:
            json.dump({
                "questao_id": q["id"],
                "imagem_mime": q["imagem_mime"],
                "imagem_b64": base64.b64encode(antiga).decode() if antiga else None,
            }, f)
        print("  backup: %s" % destino)

        cur.execute(
            "UPDATE questoes SET imagem = %s, imagem_mime = %s WHERE id = %s",
            (db.psycopg2.Binary(nova), mime, q["id"]),
        )
        con.commit()
        print("  gravado.")


if __name__ == "__main__":
    main()
