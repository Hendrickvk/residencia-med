"""
Grava o tema (questoes.subtopico_id) das questões de uma especialidade a partir
de um JSON de classificação feito lendo cada questão (fase 3 dos temas, ver
HISTORICO.md). Por padrão só simula e mostra o resumo; grava com --aplicar,
depois de salvar em backups/ o subtopico_id anterior das linhas alteradas.

    python scripts/classificar_temas.py backups/temas_obstetricia.json
    python scripts/classificar_temas.py backups/temas_obstetricia.json --aplicar

Formato: {"especialidade": "Obstetrícia", "temas": {"<id da questão>": "<nome do tema>"}}
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

    dados = json.loads(pathlib.Path(args.arquivo).read_text(encoding="utf-8"))
    classificacao = {int(qid): tema for qid, tema in dados["temas"].items()}

    with db.get_conn() as conn:
        esp = conn.execute("SELECT id FROM especialidades WHERE nome = ?", (dados["especialidade"],)).fetchone()
        if esp is None:
            sys.exit(f"Especialidade não encontrada: {dados['especialidade']}")
        temas = {t["nome"]: t["id"] for t in conn.execute(
            "SELECT id, nome FROM subtopicos WHERE especialidade_id = ? AND origem IS NULL", (esp["id"],)
        ).fetchall()}
        atuais = {q["id"]: q["subtopico_id"] for q in conn.execute(
            "SELECT id, subtopico_id FROM questoes WHERE especialidade_id = ?", (esp["id"],)
        ).fetchall()}

    erros = [f"questão {qid} não é de {dados['especialidade']}" for qid in classificacao if qid not in atuais]
    erros += [f"questão {qid}: tema desconhecido '{tema}'" for qid, tema in classificacao.items() if tema not in temas]
    if erros:
        sys.exit("Nada foi gravado:\n" + "\n".join(erros))

    novos = {qid: temas[tema] for qid, tema in classificacao.items()}
    mudam = {qid: tid for qid, tid in novos.items() if atuais[qid] != tid}
    contagem = collections.Counter(classificacao.values())
    print(f"{dados['especialidade']}: {len(classificacao)} de {len(atuais)} questões classificadas, {len(mudam)} mudam")
    for tema in sorted(temas, key=lambda nome: -contagem[nome]):
        print(f"  {contagem[tema]:3d}  {tema}")
    faltando = sorted(set(atuais) - set(classificacao))
    if faltando:
        print("Sem classificação:", faltando)

    if not args.aplicar:
        print("Simulação: nada gravado. Rode com --aplicar para gravar.")
        return
    if not mudam:
        print("Nada a gravar.")
        return

    pasta = RAIZ / "backups"
    pasta.mkdir(exist_ok=True)
    carimbo = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = pasta / f"temas_{db.normalizar_nome(dados['especialidade']).replace(' ', '_')}_{carimbo}.json"
    backup.write_text(json.dumps({qid: atuais[qid] for qid in mudam}, indent=2), encoding="utf-8")

    # Uma transação só (get_conn faz commit no fim ou desfaz tudo se algo falhar).
    with db.get_conn() as conn:
        cur = conn.execute(
            f"UPDATE questoes SET subtopico_id = v.tema FROM (VALUES {', '.join(['(?, ?)'] * len(mudam))}) "
            "AS v(id, tema) WHERE questoes.id = v.id",
            [valor for par in mudam.items() for valor in par],
        )
        print(f"Gravado: {cur.rowcount} questões. Backup do estado anterior em {backup.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
