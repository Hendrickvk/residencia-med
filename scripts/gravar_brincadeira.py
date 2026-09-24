"""Grava (ou troca) o roteiro da brincadeira de boas-vindas de uma conta.

O roteiro é pessoal e não mora no repositório, que é público: fica num JSON
fora do git (por padrão backups/brincadeira.json) e, gravado, na tabela
`brincadeiras`, que a API só entrega à própria conta (GET /me/brincadeira).
O JSON identifica a conta pelo SHA-256 do e-mail, então nem o e-mail precisa
estar escrito em lugar nenhum:

    {"email_sha256": "...", "roteiro": [...], "reprise": ["...", ...]}

Simula por padrão; grava só com --aplicar.

    python scripts/gravar_brincadeira.py
    python scripts/gravar_brincadeira.py backups/brincadeira.json --aplicar
"""

import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("arquivo", nargs="?", default=os.path.join("backups", "brincadeira.json"))
    p.add_argument("--aplicar", action="store_true")
    args = p.parse_args()

    with open(args.arquivo, encoding="utf-8") as f:
        dados = json.load(f)
    with db.get_conn() as conn:
        contas = conn.execute("SELECT id, email FROM usuarios").fetchall()
    ids = [
        c["id"] for c in contas
        if hashlib.sha256(c["email"].strip().lower().encode()).hexdigest() == dados["email_sha256"]
    ]
    if len(ids) != 1:
        sys.exit(f"Esperava uma conta com esse e-mail e achei {len(ids)}. Nada gravado.")

    print(f"Conta {ids[0]}: {len(dados['roteiro'])} passos, {len(dados['reprise'])} linhas de reprise.")
    if not args.aplicar:
        print("Simulação. Rode com --aplicar para gravar.")
        return
    db.gravar_brincadeira(ids[0], dados["roteiro"], dados["reprise"])
    print("Gravado.")


if __name__ == "__main__":
    main()
