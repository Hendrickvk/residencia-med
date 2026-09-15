"""
Grava o tema (questoes.subtopico_id) das questões de uma especialidade a partir
de um JSON de classificação feito lendo cada questão (fase 3 dos temas, ver
HISTORICO.md). Por padrão só simula e mostra o resumo; grava com --aplicar,
depois de salvar em backups/ o tema e a especialidade anteriores das linhas
alteradas.

    python scripts/classificar_temas.py backups/temas_obstetricia.json
    python scripts/classificar_temas.py backups/temas_obstetricia.json --aplicar

Formato: {"especialidade": "Obstetrícia", "temas": {"<id da questão>": "<nome do tema>"}}

O tema pode ser de outra especialidade da mesma grande área (nome de tema não
se repete dentro dela): a questão passa para essa especialidade.
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
        esp = conn.execute("SELECT id, area_id FROM especialidades WHERE nome = ?", (dados["especialidade"],)).fetchone()
        if esp is None:
            sys.exit(f"Especialidade não encontrada: {dados['especialidade']}")
        temas = {t["nome"]: t for t in conn.execute(
            "SELECT s.id, s.nome, s.especialidade_id, e.nome AS especialidade FROM subtopicos s "
            "JOIN especialidades e ON e.id = s.especialidade_id WHERE s.area_id = ? AND s.origem IS NULL",
            (esp["area_id"],),
        ).fetchall()}
        atuais = {q["id"]: q for q in conn.execute(
            "SELECT id, subtopico_id, especialidade_id FROM questoes WHERE especialidade_id = ?", (esp["id"],)
        ).fetchall()}

    erros = [f"questão {qid} não é de {dados['especialidade']}" for qid in classificacao if qid not in atuais]
    erros += [f"questão {qid}: tema desconhecido '{tema}'" for qid, tema in classificacao.items() if tema not in temas]
    if erros:
        sys.exit("Nada foi gravado:\n" + "\n".join(erros))

    novos = {qid: temas[tema] for qid, tema in classificacao.items()}
    mudam = {qid: t for qid, t in novos.items()
             if (atuais[qid]["subtopico_id"], atuais[qid]["especialidade_id"]) != (t["id"], t["especialidade_id"])}
    contagem = collections.Counter(classificacao.values())
    print(f"{dados['especialidade']}: {len(classificacao)} de {len(atuais)} questões classificadas, {len(mudam)} mudam")
    proprios = [nome for nome, t in temas.items() if t["especialidade_id"] == esp["id"]]
    for tema in sorted(proprios, key=lambda nome: -contagem[nome]):
        print(f"  {contagem[tema]:3d}  {tema}")
    for qid, t in sorted(novos.items()):
        if t["especialidade_id"] != esp["id"]:
            print(f"  questão {qid} passa para {t['especialidade']}: {t['nome']}")
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
    backup.write_text(json.dumps({
        qid: {"subtopico_id": atuais[qid]["subtopico_id"], "especialidade_id": atuais[qid]["especialidade_id"]}
        for qid in mudam
    }, indent=2), encoding="utf-8")

    # Uma transação só (get_conn faz commit no fim ou desfaz tudo se algo falhar).
    with db.get_conn() as conn:
        cur = conn.execute(
            "UPDATE questoes SET subtopico_id = v.tema, especialidade_id = v.esp "
            f"FROM (VALUES {', '.join(['(?, ?, ?)'] * len(mudam))}) AS v(id, tema, esp) WHERE questoes.id = v.id",
            [valor for qid, t in mudam.items() for valor in (qid, t["id"], t["especialidade_id"])],
        )
        print(f"Gravado: {cur.rowcount} questões. Backup do estado anterior em {backup.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
