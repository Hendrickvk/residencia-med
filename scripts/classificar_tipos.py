"""
Grava o tipo de pergunta (questoes.tipo_pergunta, ver db.TIPOS_PERGUNTA) a partir
de um JSON feito lendo as questões. Por padrão só simula e mostra o resumo; grava
com --aplicar, depois de salvar em backups/ o tipo anterior das linhas alteradas.

    python scripts/classificar_tipos.py backups/tipos_pediatria.json
    python scripts/classificar_tipos.py backups/tipos_pediatria.json --aplicar

Formato: {"tipos": {"<id da questão>": "<tipo>"}}
"""

import argparse
import collections
import datetime
import json
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import db  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("arquivo")
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()

    arquivo = pathlib.Path(args.arquivo)
    tipos = {int(qid): tipo for qid, tipo in json.loads(arquivo.read_text(encoding="utf-8"))["tipos"].items()}
    with db.get_conn() as conn:
        atuais = {q["id"]: q["tipo_pergunta"] for q in conn.execute(
            f"SELECT id, tipo_pergunta FROM questoes WHERE id IN ({', '.join(['?'] * len(tipos))})", list(tipos)
        ).fetchall()}

    erros = [f"questão {qid} não existe" for qid in tipos if qid not in atuais]
    erros += [f"questão {qid}: tipo desconhecido '{tipo}'" for qid, tipo in tipos.items() if tipo not in db.TIPOS_PERGUNTA]
    if erros:
        sys.exit("Nada foi gravado:\n" + "\n".join(erros))

    mudam = {qid: tipo for qid, tipo in tipos.items() if atuais[qid] != tipo}
    contagem = collections.Counter(tipos.values())
    print(f"{arquivo.name}: {len(tipos)} questões, {len(mudam)} mudam")
    for tipo in db.TIPOS_PERGUNTA:
        print(f"  {contagem[tipo]:4d}  {tipo}")

    if not args.aplicar:
        print("Simulação: nada gravado. Rode com --aplicar para gravar.")
        return
    if not mudam:
        print("Nada a gravar.")
        return

    carimbo = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = RAIZ / "backups" / f"{arquivo.stem}_{carimbo}.json"
    backup.parent.mkdir(exist_ok=True)
    backup.write_text(json.dumps({qid: atuais[qid] for qid in mudam}, indent=2), encoding="utf-8")

    # Uma transação só (get_conn faz commit no fim ou desfaz tudo se algo falhar).
    with db.get_conn() as conn:
        cur = conn.execute(
            f"UPDATE questoes SET tipo_pergunta = v.tipo FROM (VALUES {', '.join(['(?, ?)'] * len(mudam))}) "
            "AS v(id, tipo) WHERE questoes.id = v.id",
            [valor for par in mudam.items() for valor in par],
        )
        print(f"Gravado: {cur.rowcount} questões. Backup do estado anterior em {backup.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
