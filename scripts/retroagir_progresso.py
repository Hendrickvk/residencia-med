"""
Refaz a progressão a partir do histórico (HISTORICO.md, Gamificação): quem já
estudou não pode começar do zero. Usa as mesmas regras puras de `progressao.py`,
sobre o que já está gravado: `revisao_eventos`, `revisao_cartao_eventos`, a meta de
revisão de cada dia, as provas oficiais terminadas e, para as respostas anteriores
aos eventos, `respostas`.

Idempotente pela chave do razão: rodar de novo só acrescenta o que faltar, e o saldo
é refeito pela soma do razão. Contas de teste ficam de fora.

Por padrão simula numa transação que é desfeita no fim. Grava com --aplicar, depois
de salvar em backups/ as linhas criadas. Antes do --aplicar: `python
scripts/backup_banco.py`.

    python scripts/retroagir_progresso.py              # simula
    python scripts/retroagir_progresso.py --aplicar    # grava
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
import progressao  # noqa: E402


class Simulacao(Exception):
    """Levantada no fim da simulação para o `get_conn` desfazer a transação."""


def _quando(valor):
    return datetime.datetime.fromisoformat(valor) if isinstance(valor, str) else valor


def _linha(chave, tipo, xp, moedas, area_id, quando):
    return {"chave": chave, "tipo": tipo, "xp": xp, "moedas": moedas, "area_id": area_id, "quando": quando}


def lancamentos_de_casos(eventos, respostas, areas):
    """O que cada resposta a uma questão rendeu, na ordem em que aconteceu.
    `respostas` só conta onde não há evento naquele dia: desde que os eventos
    existem, a mesma resposta está nas duas tabelas, e o evento sabe mais (se a
    revisão tinha vencido)."""
    com_evento = {(e["questao_id"], _quando(e["registrado_em"]).date()) for e in eventos}
    linha_do_tempo = [
        (_quando(e["registrado_em"]), e["questao_id"], bool(e["correta"]), e["facilidade_antes"] is None,
         e["atraso_dias"] is not None and e["atraso_dias"] >= 0)
        for e in eventos if e["correta"] is not None
    ]
    for r in respostas:
        quando = _quando(r["respondida_em"])
        if (r["questao_id"], quando.date()) not in com_evento:
            linha_do_tempo.append((quando, r["questao_id"], bool(r["correta"]), True, False))
    linha_do_tempo.sort(key=lambda item: item[0])

    linhas = []
    vistas = set()
    pagas = set()
    acertos_do_dia = collections.Counter()
    for quando, questao_id, correta, sem_estado, vencida in linha_do_tempo:
        primeira = sem_estado and questao_id not in vistas
        vistas.add(questao_id)
        chave = progressao.chave_caso(questao_id, quando.date())
        if chave in pagas:
            continue
        pagas.add(chave)
        xp, moedas = progressao.regra_caso(primeira=primeira, vencida=vencida, correta=correta)
        if moedas:
            if acertos_do_dia[quando.date()] < progressao.ACERTOS_EM_DOBRO_POR_DIA:
                moedas *= 2
            acertos_do_dia[quando.date()] += 1
        linhas.append(_linha(chave, "caso", xp, moedas, areas.get(questao_id), quando))
    return linhas


def lancamentos_de_cartoes(eventos):
    linhas = []
    pagas = set()
    cartoes_do_dia = collections.Counter()
    for e in sorted(eventos, key=lambda e: _quando(e["registrado_em"])):
        quando = _quando(e["registrado_em"])
        chave = progressao.chave_cartao(e["cartao_id"], quando.date())
        if chave in pagas or cartoes_do_dia[quando.date()] >= progressao.TETO_CARTOES_PAGOS_DIA:
            continue
        pagas.add(chave)
        cartoes_do_dia[quando.date()] += 1
        linhas.append(_linha(chave, "cartao", progressao.XP_CARTAO, 0, None, quando))
    return linhas


def lancamentos_de_meta(eventos, meta):
    """A meta vale a de hoje: o histórico não guarda a de cada dia."""
    por_dia = collections.defaultdict(set)
    ultimo = {}
    for e in eventos:
        if e["origem"] != "revisao":
            continue
        quando = _quando(e["registrado_em"])
        por_dia[quando.date()].add(e["questao_id"])
        ultimo[quando.date()] = max(ultimo.get(quando.date(), quando), quando)
    return [
        _linha(progressao.chave_meta(dia), "meta", progressao.XP_META_REVISAO, 0, None, ultimo[dia])
        for dia, questoes in sorted(por_dia.items())
        if len(questoes) >= meta
    ]


def lancamentos_de_provas(simulados):
    linhas = []
    pagas = set()
    for s in simulados:
        xp = progressao.xp_de_prova(
            bloco=s["bloco"], num_questoes=s["num_questoes"], respondidas=s["total_respondidas"] or 0,
        )
        chave = progressao.chave_prova(s["banca"], s["edicao"], s["bloco"])
        if xp and chave not in pagas:
            pagas.add(chave)
            linhas.append(_linha(chave, "prova", xp, 0, None, _quando(s["finalizado_em"])))
    return linhas


def retroagir_conta(conn, usuario, areas):
    """Grava o que falta da conta e refaz o saldo pela soma do razão. Devolve as
    linhas criadas."""
    uid = usuario["id"]
    eventos = conn.execute("""
        SELECT questao_id, origem, correta, atraso_dias, facilidade_antes, registrado_em
        FROM revisao_eventos WHERE usuario_id = ? ORDER BY registrado_em, id
    """, (uid,)).fetchall()
    respostas = conn.execute(
        "SELECT questao_id, correta, respondida_em FROM respostas WHERE usuario_id = ? ORDER BY id", (uid,),
    ).fetchall()
    cartoes = conn.execute(
        "SELECT cartao_id, registrado_em FROM revisao_cartao_eventos WHERE usuario_id = ? ORDER BY registrado_em, id",
        (uid,),
    ).fetchall()
    simulados = conn.execute("""
        SELECT banca, edicao, bloco, num_questoes, total_respondidas, finalizado_em FROM simulados
        WHERE usuario_id = ? AND edicao IS NOT NULL AND finalizado_em IS NOT NULL ORDER BY finalizado_em
    """, (uid,)).fetchall()

    linhas = (
        lancamentos_de_casos(eventos, respostas, areas)
        + lancamentos_de_cartoes(cartoes)
        + lancamentos_de_meta(eventos, usuario["meta_revisao_diaria"])
        + lancamentos_de_provas(simulados)
    )
    criadas = []
    if linhas:
        criadas = conn.execute("""
            INSERT INTO progresso_eventos (usuario_id, chave, tipo, xp, moedas, area_id, dia, criado_em)
            SELECT ?, chave, tipo, xp, moedas, area_id, quando::date, quando
            FROM unnest(?::text[], ?::text[], ?::int[], ?::int[], ?::int[], ?::timestamp[])
                AS t(chave, tipo, xp, moedas, area_id, quando)
            ON CONFLICT (usuario_id, chave) DO NOTHING
            RETURNING chave, tipo, xp, moedas
        """, (
            uid,
            [li["chave"] for li in linhas],
            [li["tipo"] for li in linhas],
            [li["xp"] for li in linhas],
            [li["moedas"] for li in linhas],
            [li["area_id"] for li in linhas],
            [li["quando"] for li in linhas],
        )).fetchall()
    conn.execute("""
        UPDATE usuarios SET
            xp_total = (SELECT COALESCE(SUM(xp), 0) FROM progresso_eventos WHERE usuario_id = ?),
            moedas = (SELECT COALESCE(SUM(moedas), 0) FROM progresso_eventos WHERE usuario_id = ?)
        WHERE id = ?
    """, (uid, uid, uid))
    return [dict(c) for c in criadas]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--aplicar", action="store_true", help="grava em vez de simular")
    args = parser.parse_args()

    backup = {}
    try:
        with db.get_conn() as conn:
            areas = {q["id"]: q["area_id"] for q in conn.execute("SELECT id, area_id FROM questoes").fetchall()}
            contas = conn.execute(
                r"SELECT * FROM usuarios WHERE email NOT LIKE 'pytest\_%@teste.local' ORDER BY id"
            ).fetchall()
            for usuario in contas:
                criadas = retroagir_conta(conn, usuario, areas)
                saldo = conn.execute(
                    "SELECT xp_total, moedas FROM usuarios WHERE id = ?", (usuario["id"],),
                ).fetchone()
                backup[usuario["id"]] = criadas
                # Sem e-mail na saída: o id basta para conferir.
                print(
                    f"conta {usuario['id']}: {len(criadas)} lançamentos novos, {saldo['xp_total']} XP "
                    f"(nível {progressao.nivel_de(saldo['xp_total'])}), {saldo['moedas']} moedas"
                )
            if not args.aplicar:
                raise Simulacao
            destino = RAIZ / "backups" / f"retroagir_progresso_{db.agora_br():%Y%m%d_%H%M%S}.json"
            destino.parent.mkdir(exist_ok=True)
            destino.write_text(json.dumps(backup, ensure_ascii=False), encoding="utf-8")
            print(f"Linhas criadas salvas em {destino.relative_to(RAIZ)}")
    except Simulacao:
        print("Simulação desfeita. Para gravar: --aplicar (com backup_banco.py antes).")


if __name__ == "__main__":
    main()
