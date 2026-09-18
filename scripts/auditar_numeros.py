"""Lista as afirmações conferíveis das explicações: fórmula, dose por kg e referência legal.

Não julga mérito clínico: junta lado a lado as afirmações numeradas do mesmo tipo, para que
uma contradição entre duas explicações fique visível. Foi assim que se achou a Revalida
2024/2 Q17 mandando usar Parkland (4 mL x kg x %SCQ) quando o gabarito só fecha com os 2 mL
do ATLS 10ª edição — e a outra questão de queimadura do banco (Revalida 2026/1 Q60) já usava
os 2 mL, ou seja, o banco se contradizia.

Vale rodar depois de escrever as explicações de uma edição nova, como o
`auditar_explicacoes.py`. A lista inteira do banco cabe numa tela (em 2026-09-17: 2 frases de
fórmula, 18 de dose por kg, 19 de referência legal), então não precisa de filtro por edição.

    python scripts/auditar_numeros.py
    python scripts/auditar_numeros.py --banca REVALIDA --edicao 2024/2
"""

import argparse
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db

CLASSES = {
    "formula": re.compile(r"\d+[,.]?\d*\s*m[lL]\s*(?:x|×|vezes)\s*", re.I),
    "dose por kg": re.compile(r"\d+[,.]?\d*\s*(?:mg|mcg|µg|m[lL]|UI|g)\s*/\s*kg", re.I),
    "referência legal": re.compile(
        r"(?:Lei|Resolu[çc][ãa]o(?:\s+CFM)?|Portaria|ADPF|Decreto|artigo|art\.)\s*n?[º°.]?\s*[\d][\d.]*",
        re.I,
    ),
}


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--banca", help="restringe a uma banca (como está no banco: REVALIDA, USP, …)")
    p.add_argument("--edicao", help='restringe a uma edição (ex.: "2024/2")')
    args = p.parse_args()

    if bool(args.banca) != bool(args.edicao):
        p.error("--banca e --edicao vêm juntos")

    if args.banca:
        ids = db.ids_questoes_da_edicao(args.banca, args.edicao)
        if not ids:
            p.error("nenhuma questão em %s %s" % (args.banca, args.edicao))
        questoes = [db.obter_questao(qid) for qid in ids]
    else:
        with db.get_conn() as conn:
            questoes = conn.execute(
                "SELECT id, banca, edicao, ano, numero_prova, explicacao FROM questoes "
                "WHERE explicacao IS NOT NULL AND explicacao <> '' ORDER BY id"
            ).fetchall()

    achados = defaultdict(list)
    for q in questoes:
        prova = "%s %s Q%s" % (q["banca"], q["edicao"] or q["ano"], q["numero_prova"])
        for frase in re.split(r"(?<=[.!?;])\s+", q["explicacao"]):
            frase = frase.strip()
            for nome, rx in CLASSES.items():
                if frase and rx.search(frase):
                    achados[nome].append((q["id"], prova, frase))

    print("%d explicações varridas" % len(questoes))
    for nome in CLASSES:
        lista = achados[nome]
        print("\n%s — %d frase(s)" % (nome.upper(), len(lista)))
        print("-" * 78)
        for qid, prova, frase in lista:
            print("id %-5s %-22s %s" % (qid, prova, frase[:300]))


if __name__ == "__main__":
    main()
