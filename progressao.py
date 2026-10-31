"""
Progressão: XP, nível geral, nível por área e moedas (HISTORICO.md, Gamificação).

O razão é `progresso_eventos`: uma linha por ganho, com uma `chave` única por
conta. É ela que dá a idempotência (a fila de respostas pode reenviar, e o
finalizar pode ser chamado de novo) e o limite de "a mesma questão paga uma vez
por dia". O saldo fica em `usuarios.xp_total` e `usuarios.moedas`, atualizados na
mesma transação, porque o `/me` já lê essa linha a cada requisição.

As regras são funções puras, como `calcular_proximo_estado` no SM-2, e é isso que
garante que o `+10 XP` escrito na tela seja o que entra no razão, e que
`scripts/retroagir_progresso.py` refaça o histórico pela mesma conta.

Três decisões protegem o diagnóstico, e por isso `tests/test_progressao.py` as
fixa: errar também rende XP (só o acerto renderia consulta externa antes de
responder, e o Painel passaria a mentir); o chute rende igual ao seguro (senão ela
para de marcar, e a triagem e o SM-2 perdem o dado); e o cartão rende por revisar,
nunca pela nota, que é autoavaliada.
"""

import datetime

import db
from db import get_conn

XP_CERTO = 10
XP_ERRADO = 5
# Questão já vista e ainda não vencida: é estudo, mas não pode virar o jeito mais
# rápido de subir de nível.
XP_JA_VISTA = 2
XP_CARTAO = 2
# O importador aceita 2000 cartões de uma vez, e a nota é ela quem dá.
TETO_XP_CARTOES_DIA = 100
# A revisão é a única obrigação do dia, e sem isto o XP empurra para questões
# novas: na simulação de 180 dias com metas baixas, a fila passou de 800 casos.
XP_META_REVISAO = 30
XP_PROVA_INTEIRA = 100
XP_PROVA_BLOCO = 25
# Prova terminada com menos que isto respondido não é prova feita.
FRACAO_MINIMA_PROVA = 0.9

MOEDA_ACERTO = 1
# Os primeiros acertos do dia valem o dobro: o motivo para voltar amanhã.
ACERTOS_EM_DOBRO_POR_DIA = 10

# Por posto e não por pessoa, para não terem gênero. (nível em que começa, nome)
PATENTES = (
    (1, "Ciclo básico"),
    (5, "Ciclo clínico"),
    (10, "Internato"),
    (20, "R1"),
    (30, "R2"),
    (40, "R3"),
    (50, "Preceptoria"),
    (65, "Chefia"),
)

# XP para chegar a cada nível de área, do 1 ao 10. Mede trabalho, não desempenho:
# dá para ser nível 9 em Cirurgia e estar em "Urgente" no quadro do Painel.
LIMIARES_AREA = (0, 100, 300, 600, 1000, 1600, 2400, 3500, 5000, 7500)


# --- Regras (puras) ---------------------------------------------------------

def xp_do_nivel(nivel):
    """XP total para chegar ao nível. O nível 2 sai na primeira sessão; depois é
    cerca de um nível por dia no começo e um a cada 3 a 6 dias a partir do 30."""
    n = nivel - 1
    return 20 * n * n + 60 * n


def nivel_de(xp):
    nivel = 1
    while xp_do_nivel(nivel + 1) <= xp:
        nivel += 1
    return nivel


def patente_de(nivel):
    return next(nome for inicio, nome in reversed(PATENTES) if nivel >= inicio)


def progresso_do_xp(xp):
    """O nível e o quanto falta. A curva mora aqui: o front só desenha."""
    nivel = nivel_de(xp)
    base = xp_do_nivel(nivel)
    teto = xp_do_nivel(nivel + 1)
    proxima = next(({"nome": nome, "nivel": inicio} for inicio, nome in PATENTES if inicio > nivel), None)
    return {
        "xp": xp,
        "nivel": nivel,
        "patente": patente_de(nivel),
        "falta": teto - xp,
        "pct": round(100 * (xp - base) / (teto - base), 1),
        "proxima_patente": proxima,
    }


def progresso_da_area(xp):
    nivel = sum(1 for limiar in LIMIARES_AREA if xp >= limiar)
    if nivel >= len(LIMIARES_AREA):
        return {"xp": xp, "nivel": nivel, "falta": 0, "pct": 100.0}
    base = LIMIARES_AREA[nivel - 1]
    teto = LIMIARES_AREA[nivel]
    return {"xp": xp, "nivel": nivel, "falta": teto - xp, "pct": round(100 * (xp - base) / (teto - base), 1)}


def regra_caso(*, primeira, vencida, correta):
    """(xp, moedas) de responder uma questão, antes do dobro do dia. Sem parâmetro
    de confiança de propósito: o chute rende igual."""
    if not primeira and not vencida:
        return XP_JA_VISTA, 0
    return (XP_CERTO, MOEDA_ACERTO) if correta else (XP_ERRADO, 0)


def xp_de_prova(*, bloco, num_questoes, respondidas):
    if not num_questoes or respondidas / num_questoes < FRACAO_MINIMA_PROVA:
        return 0
    return XP_PROVA_BLOCO if bloco else XP_PROVA_INTEIRA


def chave_caso(questao_id, dia):
    return f"caso:{questao_id}:{dia.isoformat()}"


def chave_cartao(cartao_id, dia):
    return f"cartao:{cartao_id}:{dia.isoformat()}"


def chave_meta(dia):
    return f"meta:{dia.isoformat()}"


def chave_prova(banca, edicao, bloco):
    return f"prova:{banca}:{edicao}:{bloco or 'inteira'}"


def _ganho(*, xp, moedas, areas, total):
    antes = progresso_do_xp(total - xp)
    depois = progresso_do_xp(total)
    return {
        "xp": xp,
        "moedas": moedas,
        "areas": areas,
        "antes": antes,
        "depois": depois,
        "trocou_patente": antes["patente"] != depois["patente"],
    }


def juntar(a, b):
    """Dois ganhos da mesma resposta num só: o caso e o bônus da meta."""
    if not a or not b:
        return a or b
    areas = dict(a["areas"])
    for nome, xp in b["areas"].items():
        areas[nome] = areas.get(nome, 0) + xp
    return {
        "xp": a["xp"] + b["xp"],
        "moedas": a["moedas"] + b["moedas"],
        "areas": areas,
        "antes": a["antes"],
        "depois": b["depois"],
        "trocou_patente": a["antes"]["patente"] != b["depois"]["patente"],
    }


# --- Razão ------------------------------------------------------------------

def _lancar(conn, *, usuario_id, chave, tipo, xp, moedas, area_id, agora):
    """Uma linha no razão e o saldo, na mesma transação. Devolve o XP total
    depois do lançamento, ou None se a chave já tinha sido paga."""
    inserida = conn.execute("""
        INSERT INTO progresso_eventos (usuario_id, chave, tipo, xp, moedas, area_id, dia, criado_em)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (usuario_id, chave) DO NOTHING
    """, (usuario_id, chave, tipo, xp, moedas, area_id, agora.date(), agora)).rowcount
    if not inserida:
        return None
    return conn.execute(
        "UPDATE usuarios SET xp_total = xp_total + ?, moedas = moedas + ? WHERE id = ? RETURNING xp_total",
        (xp, moedas, usuario_id),
    ).fetchone()["xp_total"]


def pontuar_casos(conn, *, usuario_id, casos, agora):
    """Paga as respostas a questões, dentro da transação de quem grava a revisão
    (`sr.registrar_revisao`, por onde passam Praticar e Revisão, uma de cada vez, e
    `sr.registrar_simulado`, a prova inteira de uma vez). Cada caso traz `questao_id`,
    `primeira`, `vencida` e `correta`. O número de idas ao banco não depende de
    quantos são. Devolve o ganho somado, ou None se nenhuma questão pagou (a mesma
    questão só paga uma vez por dia)."""
    dia = agora.date()
    hoje = conn.execute(
        "SELECT chave, moedas FROM progresso_eventos WHERE usuario_id = ? AND dia = ? AND tipo = 'caso'",
        (usuario_id, dia),
    ).fetchall()
    pagas = {linha["chave"] for linha in hoje}
    acertos = sum(1 for linha in hoje if linha["moedas"] > 0)
    questoes = {
        q["id"]: q
        for q in conn.execute("""
            SELECT q.id, q.area_id, a.nome AS area FROM questoes q
            LEFT JOIN areas a ON a.id = q.area_id
            WHERE q.id = ANY(?)
        """, ([caso["questao_id"] for caso in casos],)).fetchall()
    }

    linhas = []
    for caso in casos:
        chave = chave_caso(caso["questao_id"], dia)
        if chave in pagas:
            continue
        pagas.add(chave)
        xp, moedas = regra_caso(primeira=caso["primeira"], vencida=caso["vencida"], correta=caso["correta"])
        if moedas:
            if acertos < ACERTOS_EM_DOBRO_POR_DIA:
                moedas *= 2
            acertos += 1
        questao = questoes[caso["questao_id"]]
        linhas.append({"chave": chave, "xp": xp, "moedas": moedas, "area_id": questao["area_id"], "area": questao["area"]})
    if not linhas:
        return None

    # RETURNING, e não confiar em `pagas`: outra aba pode ter pago a mesma questão
    # entre a leitura e aqui, e é a chave única que decide.
    criadas = {
        r["chave"]
        for r in conn.execute("""
            INSERT INTO progresso_eventos (usuario_id, chave, tipo, xp, moedas, area_id, dia, criado_em)
            SELECT ?, chave, 'caso', xp, moedas, area_id, ?, ?
            FROM unnest(?::text[], ?::int[], ?::int[], ?::int[]) AS t(chave, xp, moedas, area_id)
            ON CONFLICT (usuario_id, chave) DO NOTHING
            RETURNING chave
        """, (
            usuario_id, dia, agora,
            [li["chave"] for li in linhas], [li["xp"] for li in linhas],
            [li["moedas"] for li in linhas], [li["area_id"] for li in linhas],
        )).fetchall()
    }
    linhas = [li for li in linhas if li["chave"] in criadas]
    if not linhas:
        return None

    xp = sum(li["xp"] for li in linhas)
    moedas = sum(li["moedas"] for li in linhas)
    total = conn.execute(
        "UPDATE usuarios SET xp_total = xp_total + ?, moedas = moedas + ? WHERE id = ? RETURNING xp_total",
        (xp, moedas, usuario_id),
    ).fetchone()["xp_total"]
    areas = {}
    for li in linhas:
        areas[li["area"]] = areas.get(li["area"], 0) + li["xp"]
    return _ganho(xp=xp, moedas=moedas, areas=areas, total=total)


def pontuar_cartao(cartao_id, *, usuario_id, agora):
    """O cartão rende por ter sido revisado, seja qual for a nota. Desfazer a nota
    não devolve o XP, e a chave impede pagar de novo o mesmo cartão no dia."""
    dia = agora.date()
    with get_conn() as conn:
        hoje = conn.execute("""
            SELECT COALESCE(SUM(xp), 0) AS xp FROM progresso_eventos
            WHERE usuario_id = ? AND dia = ? AND tipo = 'cartao'
        """, (usuario_id, dia)).fetchone()["xp"]
        if hoje + XP_CARTAO > TETO_XP_CARTOES_DIA:
            return None
        total = _lancar(
            conn, usuario_id=usuario_id, chave=chave_cartao(cartao_id, dia), tipo="cartao", xp=XP_CARTAO,
            moedas=0, area_id=None, agora=agora,
        )
    if total is None:
        return None
    return _ganho(xp=XP_CARTAO, moedas=0, areas={}, total=total)


def pontuar_meta_revisao(*, usuario_id, feitas, agora):
    """O bônus de cumprir a meta de revisão do dia, uma vez por dia."""
    with get_conn() as conn:
        meta = conn.execute(
            "SELECT meta_revisao_diaria FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()["meta_revisao_diaria"]
        if feitas < meta:
            return None
        total = _lancar(
            conn, usuario_id=usuario_id, chave=chave_meta(agora.date()), tipo="meta", xp=XP_META_REVISAO,
            moedas=0, area_id=None, agora=agora,
        )
    if total is None:
        return None
    return _ganho(xp=XP_META_REVISAO, moedas=0, areas={}, total=total)


def fechar_simulado(simulado_id, *, usuario_id, ganhos, agora):
    """Depois de consolidar as respostas: o bônus da prova oficial e o total que o
    resultado mostra mesmo depois de recarregar a página. Devolve os ganhos."""
    ganhos = [g for g in ganhos if g]
    with get_conn() as conn:
        simulado = conn.execute(
            "SELECT * FROM simulados WHERE id = ? AND usuario_id = ?", (simulado_id, usuario_id)
        ).fetchone()
        if simulado["edicao"]:
            xp = xp_de_prova(
                bloco=simulado["bloco"], num_questoes=simulado["num_questoes"],
                respondidas=simulado["total_respondidas"] or 0,
            )
            if xp:
                total = _lancar(
                    conn, usuario_id=usuario_id, chave=chave_prova(simulado["banca"], simulado["edicao"], simulado["bloco"]),
                    tipo="prova", xp=xp, moedas=0, area_id=None, agora=agora,
                )
                if total is not None:
                    ganhos.append(_ganho(xp=xp, moedas=0, areas={}, total=total))
        conn.execute(
            "UPDATE simulados SET xp_ganho = ?, moedas_ganhas = ? WHERE id = ?",
            (sum(g["xp"] for g in ganhos), sum(g["moedas"] for g in ganhos), simulado_id),
        )
    return ganhos


# --- Leitura ----------------------------------------------------------------

def prever_casos(questao_ids, *, usuario_id):
    """{questao_id: {"certo": xp, "errado": xp}} de um lote, pela mesma regra que
    paga: o feedback é local e a resposta só é gravada depois, então o `+10 XP` da
    discussão vem daqui, como os prazos da Revisão vêm de `prever_prazos`."""
    ids = list(questao_ids)
    if not ids:
        return {}
    agora = db.agora_br()
    dia = agora.date()
    with get_conn() as conn:
        vence_em = {
            r["questao_id"]: r["proxima_revisao"]
            for r in conn.execute(
                "SELECT questao_id, proxima_revisao FROM revisao WHERE usuario_id = ? AND questao_id = ANY(?)",
                (usuario_id, ids),
            ).fetchall()
        }
        pagas = {
            r["chave"]
            for r in conn.execute(
                "SELECT chave FROM progresso_eventos WHERE usuario_id = ? AND dia = ? AND tipo = 'caso'",
                (usuario_id, dia),
            ).fetchall()
        }
    previsao = {}
    for questao_id in ids:
        if chave_caso(questao_id, dia) in pagas:
            previsao[questao_id] = {"certo": 0, "errado": 0}
            continue
        primeira = questao_id not in vence_em
        vencida = not primeira and vence_em[questao_id] <= agora
        previsao[questao_id] = {
            "certo": regra_caso(primeira=primeira, vencida=vencida, correta=True)[0],
            "errado": regra_caso(primeira=primeira, vencida=vencida, correta=False)[0],
        }
    return previsao


def resumo(usuario):
    """O que a página `/progresso` mostra."""
    usuario_id = usuario["id"]
    hoje = db.hoje_br()
    desde = hoje - datetime.timedelta(days=181)
    with get_conn() as conn:
        areas = conn.execute("""
            SELECT a.id, a.nome, COALESCE(SUM(e.xp), 0) AS xp FROM areas a
            LEFT JOIN progresso_eventos e ON e.area_id = a.id AND e.usuario_id = ?
            GROUP BY a.id, a.nome
        """, (usuario_id,)).fetchall()
        dias = conn.execute("""
            SELECT dia, SUM(xp) AS xp FROM progresso_eventos
            WHERE usuario_id = ? AND dia >= ?
            GROUP BY dia ORDER BY dia
        """, (usuario_id, desde)).fetchall()

    maior = atual = 0
    anterior = None
    for linha in dias:
        atual = atual + 1 if anterior and linha["dia"] - anterior == datetime.timedelta(days=1) else 1
        maior = max(maior, atual)
        anterior = linha["dia"]

    return {
        "nivel": progresso_do_xp(usuario["xp_total"]),
        "patentes": [{"nome": nome, "nivel": inicio} for inicio, nome in PATENTES],
        # As cinco grandes áreas, mesmo sem XP; outra área só aparece se tiver rendido algo.
        "areas": sorted(
            (
                {"id": a["id"], "nome": a["nome"], **progresso_da_area(a["xp"])}
                for a in areas
                if a["nome"] in db.TAXONOMIA or a["xp"] > 0
            ),
            key=lambda a: (-a["xp"], a["nome"]),
        ),
        "hoje": hoje,
        "dias": [{"dia": d["dia"], "xp": d["xp"]} for d in dias],
        "maior_sequencia": maior,
    }
