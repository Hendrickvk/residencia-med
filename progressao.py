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
import json

import db
from db import get_conn

XP_CERTO = 10
XP_ERRADO = 5
# Questão já vista e ainda não vencida: é estudo, mas não pode virar o jeito mais
# rápido de subir de nível.
XP_JA_VISTA = 2
XP_CARTAO = 2
# O importador aceita 2000 cartões de uma vez, e a nota é ela quem dá. Em cartões, e
# não em XP, para o XP em dobro não encurtar o teto.
TETO_CARTOES_PAGOS_DIA = 50
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

# --- Loja -------------------------------------------------------------------
# A loja nunca vende ajuda na questão, dinheiro de verdade não entra e não há caixa
# surpresa (HISTORICO.md, Gamificação). Cada item pede nível (ou nível de área) e
# moedas: são dois motivos para continuar. **O `id` de item publicado nunca muda**: é
# o que fica no razão e em `usuarios.equipados`, e o desenho mora no front, por id
# (`lib/cosmeticos.ts`), nunca vindo de fora.
PROTECAO_OFENSIVA = "protecao-ofensiva"
PRECO_PROTECAO = 60
MAXIMO_PROTECOES = 2
XP_EM_DOBRO = "xp-em-dobro"
PRECO_XP_DOBRO = 40
MINUTOS_XP_DOBRO = 30
SEM_MOLDURA = "nenhuma"

_ROTULO_DO_TIPO = {"moldura": "a moldura", "titulo": "o título"}

# A moldura de cada patente vem de graça ao chegar nela. Ciclo básico não tem.
_MOLDURAS_DE_PATENTE = {
    "Ciclo clínico": "ciclo",
    "Internato": "sutura",
    "R1": "residencia",
    "R2": "r2",
    "R3": "r3",
    "Preceptoria": "preceptoria",
    "Chefia": "chefia",
}

CATALOGO = (
    *(
        {"id": id_, "tipo": "moldura", "nome": patente, "preco": 0, "nivel": inicio, "de_patente": True}
        for inicio, patente in PATENTES
        for id_ in [_MOLDURAS_DE_PATENTE.get(patente)]
        if id_
    ),
    {"id": "pontos", "tipo": "moldura", "nome": "Ponteado", "preco": 200, "nivel": 5},
    {"id": "milimetrado", "tipo": "moldura", "nome": "Milimetrado", "preco": 250, "nivel": 10},
    {"id": "plantao", "tipo": "moldura", "nome": "Plantão", "preco": 400, "nivel": 15},
    {"id": "estetoscopio", "tipo": "moldura", "nome": "Estetoscópio", "preco": 500, "nivel": 20},
    {"id": "monitor", "tipo": "moldura", "nome": "Monitor", "preco": 650, "nivel": 25},
    {"id": "monitor-ouro", "tipo": "moldura", "nome": "Monitor de ouro", "preco": 1200, "nivel": 40},
    {"id": "plantonista", "tipo": "titulo", "nome": "Plantonista", "preco": 100, "nivel": 8},
    {"id": "noite-de-plantao", "tipo": "titulo", "nome": "Noite de plantão", "preco": 150, "nivel": 15},
    {"id": "segunda-opiniao", "tipo": "titulo", "nome": "Segunda opinião", "preco": 250, "nivel": 25},
    {"id": "terapia-intensiva", "tipo": "titulo", "nome": "Terapia intensiva", "preco": 300, "nivel": 35},
    {"id": "caso-raro", "tipo": "titulo", "nome": "Caso raro", "preco": 300, "nivel": 45},
    {"id": "mao-de-cirurgiao", "tipo": "titulo", "nome": "Mão de cirurgião", "preco": 200,
     "area": "Cirurgia", "nivel_area": 5},
    {"id": "raciocinio-clinico", "tipo": "titulo", "nome": "Raciocínio clínico", "preco": 200,
     "area": "Clínica Médica", "nivel_area": 5},
    {"id": "sala-de-parto", "tipo": "titulo", "nome": "Sala de parto", "preco": 200,
     "area": "Ginecologia e Obstetrícia", "nivel_area": 5},
    {"id": "puericultura", "tipo": "titulo", "nome": "Puericultura", "preco": 200,
     "area": "Pediatria", "nivel_area": 5},
    {"id": "saude-coletiva", "tipo": "titulo", "nome": "Saúde coletiva", "preco": 200,
     "area": "Medicina Preventiva e Social", "nivel_area": 5},
)
ITENS = {item["id"]: item for item in CATALOGO}


class ItemInexistente(Exception):
    pass


class CompraRecusada(Exception):
    """A mensagem é para a tela: nível, saldo, item que já é dela."""


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


def proximo_desbloqueio(nivel):
    """O próximo nível que libera alguma coisa, e o quê: é o que a tela promete
    ("No nível 15 você libera a moldura Plantão"), porque item travado à vista é o
    que dá vontade de chegar lá."""
    proximo = min((i["nivel"] for i in CATALOGO if i.get("nivel", 0) > nivel), default=None)
    if proximo is None:
        return None
    itens = [i for i in CATALOGO if i.get("nivel") == proximo]
    nomes = [f"{_ROTULO_DO_TIPO[i['tipo']]} {i['nome']}" for i in itens]
    frase = nomes[0] if len(nomes) == 1 else f"{', '.join(nomes[:-1])} e {nomes[-1]}"
    return {
        "nivel": proximo,
        "frase": frase,
        "itens": [
            {"id": i["id"], "tipo": i["tipo"], "nome": i["nome"], "preco": i["preco"], "de_patente": bool(i.get("de_patente"))}
            for i in itens
        ],
    }


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
        "libera": proximo_desbloqueio(nivel),
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


def dias_a_proteger(estudo, protegidos, hoje, disponiveis):
    """Os dias sem estudo entre o último dia da ofensiva e hoje, se as proteções
    guardadas cobrem todos. Se não cobrem, nenhum: gastar duas proteções para perder
    a ofensiva do mesmo jeito seria o pior dos dois mundos."""
    anteriores = [dia for dia in estudo | protegidos if dia < hoje]
    if not anteriores:
        return []
    ultimo = max(anteriores)
    buraco = [ultimo + datetime.timedelta(days=i) for i in range(1, (hoje - ultimo).days)]
    return buraco if len(buraco) <= disponiveis else []


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


def _xp_em_dobro(conn, usuario_id, agora):
    ate = conn.execute("SELECT xp_dobro_ate FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()["xp_dobro_ate"]
    return ate is not None and ate > agora


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
    dobro = _xp_em_dobro(conn, usuario_id, agora)
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
        linhas.append({
            "chave": chave, "xp": xp * (2 if dobro else 1), "moedas": moedas,
            "area_id": questao["area_id"], "area": questao["area"],
        })
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
        pagos = conn.execute("""
            SELECT COUNT(*) AS n FROM progresso_eventos
            WHERE usuario_id = ? AND dia = ? AND tipo = 'cartao'
        """, (usuario_id, dia)).fetchone()["n"]
        if pagos >= TETO_CARTOES_PAGOS_DIA:
            return None
        xp = XP_CARTAO * (2 if _xp_em_dobro(conn, usuario_id, agora) else 1)
        total = _lancar(
            conn, usuario_id=usuario_id, chave=chave_cartao(cartao_id, dia), tipo="cartao", xp=xp,
            moedas=0, area_id=None, agora=agora,
        )
    if total is None:
        return None
    return _ganho(xp=xp, moedas=0, areas={}, total=total)


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
        # Só com ganho: a chamada repetida não tem nada a somar, e não pode zerar o total.
        if ganhos:
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
        fator = 2 if _xp_em_dobro(conn, usuario_id, agora) else 1
    previsao = {}
    for questao_id in ids:
        if chave_caso(questao_id, dia) in pagas:
            previsao[questao_id] = {"certo": 0, "errado": 0}
            continue
        primeira = questao_id not in vence_em
        vencida = not primeira and vence_em[questao_id] <= agora
        previsao[questao_id] = {
            "certo": regra_caso(primeira=primeira, vencida=vencida, correta=True)[0] * fator,
            "errado": regra_caso(primeira=primeira, vencida=vencida, correta=False)[0] * fator,
        }
    return previsao


def bonus_do_dia(*, usuario_id):
    """Quantos dos acertos em dobro de hoje já saíram: o motivo para voltar amanhã,
    na faixa do Painel."""
    with get_conn() as conn:
        feitos = conn.execute("""
            SELECT COUNT(*) AS n FROM progresso_eventos
            WHERE usuario_id = ? AND dia = ? AND tipo = 'caso' AND moedas > 0
        """, (usuario_id, db.hoje_br())).fetchone()["n"]
    return {"feitos": min(feitos, ACERTOS_EM_DOBRO_POR_DIA), "total": ACERTOS_EM_DOBRO_POR_DIA}


def usar_protecoes(usuario, estudo, protegidos):
    """Gasta as proteções que cobrem o buraco na ofensiva e devolve os dias
    protegidos agora. Roda no `/me`, a primeira coisa que o app pergunta quando ela
    volta. Primeiro o INSERT, e o desconto só do que entrou: dois `/me` ao mesmo
    tempo não gastam duas vezes a proteção do mesmo dia."""
    disponiveis = usuario["protecoes_ofensiva"]
    if not disponiveis:
        return set()
    buraco = dias_a_proteger(estudo, protegidos, db.hoje_br(), disponiveis)
    if not buraco:
        return set()
    with get_conn() as conn:
        novos = conn.execute("""
            INSERT INTO ofensiva_protecoes (usuario_id, dia)
            SELECT ?, dia FROM unnest(?::date[]) AS t(dia)
            ON CONFLICT (usuario_id, dia) DO NOTHING
            RETURNING dia
        """, (usuario["id"], buraco)).fetchall()
        if novos:
            conn.execute(
                "UPDATE usuarios SET protecoes_ofensiva = protecoes_ofensiva - ? WHERE id = ?",
                (len(novos), usuario["id"]),
            )
    return set(buraco)


def equipados_de(usuario):
    """O que aparece no crachá e no menu da conta: o id da moldura (quem desenha é o
    front) e o nome do título. Sem escolha, a moldura é a da patente: quem nunca
    entrou na loja também troca de moldura ao trocar de patente."""
    equipados = usuario["equipados"] or {}
    moldura = equipados.get("moldura") or _MOLDURAS_DE_PATENTE.get(patente_de(nivel_de(usuario["xp_total"])))
    titulo = ITENS.get(equipados.get("titulo"))
    return {
        "moldura": None if moldura == SEM_MOLDURA else moldura,
        "titulo": titulo["nome"] if titulo else None,
    }


def _xp_por_area(conn, usuario_id):
    return {
        a["nome"]: a["xp"]
        for a in conn.execute("""
            SELECT a.nome, SUM(e.xp) AS xp FROM progresso_eventos e
            JOIN areas a ON a.id = e.area_id
            WHERE e.usuario_id = ?
            GROUP BY a.nome
        """, (usuario_id,)).fetchall()
    }


def _compradas(conn, usuario_id):
    return {
        r["chave"].split(":")[1]
        for r in conn.execute(
            "SELECT chave FROM progresso_eventos WHERE usuario_id = ? AND tipo = 'compra'", (usuario_id,),
        ).fetchall()
    }


def _liberado(item, nivel, xp_por_area):
    if "area" in item:
        return progresso_da_area(xp_por_area.get(item["area"], 0))["nivel"] >= item["nivel_area"]
    return nivel >= item["nivel"]


def _exigencia(item):
    if "area" in item:
        return f"Nível {item['nivel_area']} em {item['area']}"
    return f"Nível {item['nivel']}"


def loja(usuario_id):
    """A loja inteira, com o estado de cada item para esta conta. A tela só desenha:
    quem decide o que está liberado, o que é dela e o que está em uso é aqui."""
    agora = db.agora_br()
    with get_conn() as conn:
        linha = conn.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        xp_por_area = _xp_por_area(conn, usuario_id)
        compradas = _compradas(conn, usuario_id)
    nivel = nivel_de(linha["xp_total"])
    equipados = linha["equipados"] or {}
    moldura_em_uso = equipados_de(linha)["moldura"]

    def estado(item):
        de_patente = bool(item.get("de_patente"))
        liberado = _liberado(item, nivel, xp_por_area)
        em_uso = moldura_em_uso == item["id"] if item["tipo"] == "moldura" else equipados.get("titulo") == item["id"]
        return {
            "id": item["id"],
            "tipo": item["tipo"],
            "nome": item["nome"],
            "preco": item["preco"],
            "exige": _exigencia(item),
            "de_patente": de_patente,
            "liberado": liberado,
            "seu": (de_patente and liberado) or item["id"] in compradas,
            "em_uso": em_uso,
        }

    dobro_ate = linha["xp_dobro_ate"] if linha["xp_dobro_ate"] and linha["xp_dobro_ate"] > agora else None
    return {
        "moedas": linha["moedas"],
        "nivel": nivel,
        "protecao": {
            "id": PROTECAO_OFENSIVA, "preco": PRECO_PROTECAO,
            "tem": linha["protecoes_ofensiva"], "maximo": MAXIMO_PROTECOES,
        },
        "xp_dobro": {"id": XP_EM_DOBRO, "preco": PRECO_XP_DOBRO, "minutos": MINUTOS_XP_DOBRO, "ate": dobro_ate},
        "secoes": [
            {
                "tipo": tipo,
                "nome": nome,
                # O liberado primeiro. Ser dela não entra na ordem: o item recém-comprado
                # sairia de baixo do dedo.
                "itens": sorted(
                    (estado(i) for i in CATALOGO if i["tipo"] == tipo),
                    key=lambda i: (not i["liberado"], ITENS[i["id"]].get("nivel", 0)),
                ),
            }
            for tipo, nome in (("moldura", "Molduras"), ("titulo", "Títulos"))
        ],
    }


def _pagar(conn, *, usuario_id, chave, preco, agora):
    """A compra no razão e no saldo, na transação de quem chama. A chave única segura
    o mesmo item comprado duas vezes, e o `moedas >= preco` no próprio UPDATE segura
    duas compras ao mesmo tempo com saldo para uma: a segunda espera a trava da linha
    e já não acha saldo. Levantar a exceção desfaz a transação inteira."""
    inserida = conn.execute("""
        INSERT INTO progresso_eventos (usuario_id, chave, tipo, moedas, dia, criado_em)
        VALUES (?, ?, 'compra', ?, ?, ?)
        ON CONFLICT (usuario_id, chave) DO NOTHING
    """, (usuario_id, chave, -preco, agora.date(), agora)).rowcount
    if not inserida:
        raise CompraRecusada("Este item já é seu.")
    pago = conn.execute(
        "UPDATE usuarios SET moedas = moedas - ? WHERE id = ? AND moedas >= ?", (preco, usuario_id, preco),
    ).rowcount
    if not pago:
        raise CompraRecusada("Faltam moedas para este item.")


def comprar(item_id, *, usuario_id):
    agora = db.agora_br()
    with get_conn() as conn:
        if item_id == PROTECAO_OFENSIVA:
            guardou = conn.execute(
                "UPDATE usuarios SET protecoes_ofensiva = protecoes_ofensiva + 1 WHERE id = ? AND protecoes_ofensiva < ?",
                (usuario_id, MAXIMO_PROTECOES),
            ).rowcount
            if not guardou:
                raise CompraRecusada(f"Dá para guardar até {MAXIMO_PROTECOES} proteções.")
            _pagar(conn, usuario_id=usuario_id, chave=f"compra:{item_id}:{agora.isoformat()}",
                   preco=PRECO_PROTECAO, agora=agora)
        elif item_id == XP_EM_DOBRO:
            ligou = conn.execute("""
                UPDATE usuarios SET xp_dobro_ate = ?
                WHERE id = ? AND (xp_dobro_ate IS NULL OR xp_dobro_ate <= ?)
            """, (agora + datetime.timedelta(minutes=MINUTOS_XP_DOBRO), usuario_id, agora)).rowcount
            if not ligou:
                raise CompraRecusada("O XP em dobro já está valendo.")
            _pagar(conn, usuario_id=usuario_id, chave=f"compra:{item_id}:{agora.isoformat()}",
                   preco=PRECO_XP_DOBRO, agora=agora)
        else:
            item = ITENS.get(item_id)
            if item is None:
                raise ItemInexistente(item_id)
            if item.get("de_patente"):
                raise CompraRecusada("Esta moldura vem com a patente.")
            xp_total = conn.execute("SELECT xp_total FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()["xp_total"]
            if not _liberado(item, nivel_de(xp_total), _xp_por_area(conn, usuario_id)):
                raise CompraRecusada(f"Este item ainda não foi liberado. Pede: {_exigencia(item)}.")
            _pagar(conn, usuario_id=usuario_id, chave=f"compra:{item_id}", preco=item["preco"], agora=agora)
    return loja(usuario_id)


def equipar(tipo, item_id, *, usuario_id):
    """`item_id` None tira o que está em uso. Sem moldura é uma escolha gravada: sem
    ela, a moldura da patente volta sozinha."""
    if tipo not in ("moldura", "titulo"):
        raise ItemInexistente(tipo)
    with get_conn() as conn:
        linha = conn.execute("SELECT xp_total, equipados FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        if item_id is None:
            valor = SEM_MOLDURA if tipo == "moldura" else None
        else:
            item = ITENS.get(item_id)
            if item is None or item["tipo"] != tipo:
                raise ItemInexistente(item_id)
            if item.get("de_patente"):
                seu = nivel_de(linha["xp_total"]) >= item["nivel"]
            else:
                seu = item_id in _compradas(conn, usuario_id)
            if not seu:
                raise CompraRecusada("Este item ainda não é seu.")
            valor = item_id
        equipados = {**(linha["equipados"] or {}), tipo: valor}
        conn.execute("UPDATE usuarios SET equipados = ?::jsonb WHERE id = ?", (json.dumps(equipados), usuario_id))
    return loja(usuario_id)


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
            WHERE usuario_id = ? AND dia >= ? AND xp > 0
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
