"""
Conquistas: a caderneta de carimbos (HISTORICO.md, Gamificação).

Cada carimbo é um limite sobre uma medida do histórico: `medir` lê o histórico da
conta e diz quanto ela tem de cada coisa, e o carimbo sai quando a medida alcança o
alvo. Por isso não há uma regra por tela nem evento a perder: o que aconteceu antes
de a conquista existir conta do mesmo jeito (`scripts/retroagir_progresso.py`).

Ter o carimbo é ter a linha `conquista:{id}` no razão, que paga as moedas uma vez só
e guarda a data. Como na loja, não há tabela própria.

A avaliação roda no fim da sessão e ao abrir a caderneta, e não a cada resposta: o
caso fica sóbrio (DESIGN_TRIAGEM.md §6), e cada resposta não precisa pagar dez idas
ao banco. Os ids não mudam nunca: estão gravados no razão.
"""

import collections

import db
import progressao
import repeticao_espacada as sr
from db import get_conn

# A triagem de uma área só vale com volume: com 5 respostas, uma sequência de sorte já
# a pintaria de azul. As faixas são as de `frontend/src/lib/triagem.ts`.
RESPOSTAS_MINIMAS_AREA = 20
FAIXA_EMERGENCIA = 40
FAIXA_VERDE = 60
FAIXA_AZUL = 70
RESPOSTAS_MINIMAS_PROJECAO = 100

ORDEM_GRAU = {"bronze": 0, "prata": 1, "ouro": 2}


def _carimbo(id, nome, grau, moedas, medida, alvo, nota=None, dica=None, secreta=False):
    return {"id": id, "nome": nome, "grau": grau, "moedas": moedas, "medida": medida, "alvo": alvo,
            "nota": nota, "dica": dica, "secreta": secreta}


def _nivel_area(id, nome, area):
    return _carimbo(id, nome, "bronze", 25, f"nivel:{area}", 5, nota="Nível {v} de {a}")


SERIES = [
    ("Ofensiva", [
        _carimbo("ofensiva-3", "Três dias seguidos", "bronze", 15, "ofensiva", 3, nota="{v} de {a} dias"),
        _carimbo("ofensiva-7", "Sete dias seguidos", "prata", 50, "ofensiva", 7, nota="{v} de {a} dias"),
        _carimbo("ofensiva-14", "Catorze dias", "prata", 75, "ofensiva", 14, nota="{v} de {a} dias"),
        _carimbo("ofensiva-30", "Trinta dias", "prata", 100, "ofensiva", 30, nota="{v} de {a} dias"),
        _carimbo("ofensiva-60", "Sessenta dias", "ouro", 200, "ofensiva", 60, nota="{v} de {a} dias"),
        _carimbo("ofensiva-100", "Cem dias", "ouro", 300, "ofensiva", 100, nota="{v} de {a} dias"),
    ]),
    ("Casos", [
        _carimbo("casos-1", "Primeiro caso", "bronze", 10, "casos", 1, dica="Responda o primeiro caso"),
        _carimbo("certos-10", "Dez certos seguidos", "bronze", 20, "certos_seguidos", 10, nota="Melhor: {v} de {a}"),
        _carimbo("casos-100", "Cem casos", "bronze", 25, "casos", 100, nota="{v} de {a}"),
        _carimbo("casos-500", "Quinhentos casos", "prata", 75, "casos", 500, nota="{v} de {a}"),
        _carimbo("casos-1000", "Mil casos", "prata", 100, "casos", 1000, nota="{v} de {a}"),
        _carimbo("casos-todos", "Todos os casos", "ouro", 300, "banco_pct", 100, nota="{v}% do banco"),
    ]),
    ("Memória", [
        _carimbo("revisao-1", "Primeira revisão", "bronze", 10, "revisoes", 1, dica="Faça a primeira revisão"),
        _carimbo("recuperou-10", "Recuperou 10 casos", "bronze", 25, "recuperados", 10, nota="{v} de {a}"),
        _carimbo("recuperou-50", "Recuperou 50 casos", "prata", 75, "recuperados", 50, nota="{v} de {a}"),
        _carimbo("recuperou-100", "Recuperou 100 casos", "ouro", 150, "recuperados", 100, nota="{v} de {a}"),
        _carimbo("consolidou-100", "Consolidou 100 casos", "prata", 75, "consolidados", 100, nota="{v} de {a}"),
        _carimbo("consolidou-500", "Consolidou 500 casos", "ouro", 250, "consolidados", 500, nota="{v} de {a}"),
    ]),
    ("Triagem", [
        _carimbo("saiu-emergencia", "Saiu da Emergência", "prata", 75, "saiu_emergencia", 1,
                 dica="Tire uma área de Emergência"),
        _carimbo("area-verde", "Primeira área no verde", "prata", 50, "areas_verdes_max", 1,
                 dica="Uma área em 60% ou mais"),
        _carimbo("acima-corte", "Acima do corte", "ouro", 200, "acima_corte", 1,
                 dica="Nota projetada acima do corte"),
        _carimbo("cinco-verde", "Cinco áreas no verde", "ouro", 300, "areas_verdes_max", 5, nota="Melhor: {v} de {a} áreas"),
        _carimbo("sem-vermelho", "Nenhuma área em vermelho", "prata", 100, "sem_vermelho", 1,
                 dica="As cinco áreas fora de Emergência"),
        _carimbo("tudo-azul", "Tudo em azul", "ouro", 300, "areas_azuis_max", 5, nota="Melhor: {v} de {a} áreas"),
    ]),
    ("Provas oficiais", [
        _carimbo("prova-1", "Primeira prova", "prata", 50, "provas", 1, dica="Termine uma prova oficial"),
        _carimbo("prova-blocos", "Prova em blocos", "bronze", 25, "provas_em_blocos", 1,
                 dica="Termine todos os blocos de uma prova"),
        _carimbo("prova-corte", "Acima do corte numa prova", "ouro", 150, "prova_acima_corte", 1,
                 dica="Só provas com corte em acertos"),
        _carimbo("prova-duas-bancas", "Revalida e ENAMED", "prata", 75, "bancas_inep", 2, nota="{v} de {a} bancas"),
        _carimbo("prova-usp", "USP", "bronze", 25, "banca:USP", 1, dica="Faça a prova da USP"),
        _carimbo("prova-unicamp", "UNICAMP", "bronze", 25, "banca:UNICAMP", 1, dica="Faça a prova da UNICAMP"),
    ]),
    ("Experiência por área", [
        _nivel_area("area-clinica-5", "Clínica nível 5", "Clínica Médica"),
        _nivel_area("area-cirurgia-5", "Cirurgia nível 5", "Cirurgia"),
        _nivel_area("area-go-5", "Ginecologia nível 5", "Ginecologia e Obstetrícia"),
        _nivel_area("area-pediatria-5", "Pediatria nível 5", "Pediatria"),
        _nivel_area("area-preventiva-5", "Preventiva nível 5", "Medicina Preventiva e Social"),
        _carimbo("areas-nivel-10", "Cinco áreas no nível 10", "ouro", 300, "areas_nivel_10", 5, nota="{v} de {a} áreas"),
    ]),
    ("Cartões", [
        _carimbo("cartao-1", "Primeiro cartão", "bronze", 10, "cartoes", 1, dica="Revise o primeiro cartão"),
        _carimbo("cartoes-100", "Cem cartões", "bronze", 25, "cartoes", 100, nota="{v} de {a}"),
        _carimbo("cartoes-500", "Quinhentos cartões", "prata", 50, "cartoes", 500, nota="{v} de {a}"),
        _carimbo("cartoes-1000", "Mil cartões", "prata", 75, "cartoes", 1000, nota="{v} de {a}"),
    ]),
    ("Outros", [
        _carimbo("olho-clinico", "Olho clínico", "prata", 50, "relatos_resolvidos", 1, dica="Um relato de erro resolvido"),
        _carimbo("de-volta", "De volta ao plantão", "bronze", 25, "maior_ausencia", 30, secreta=True),
        _carimbo("cem-num-dia", "Cem casos num dia", "prata", 50, "casos_num_dia", 100, secreta=True),
        _carimbo("todas-as-provas", "Todas as provas", "ouro", 150, "provas_pct", 100, secreta=True),
    ]),
]

CONQUISTAS = [c for _, carimbos in SERIES for c in carimbos]
PORTE = {c["id"]: c for c in CONQUISTAS}


def chave(id_conquista):
    return f"conquista:{id_conquista}"


# --- Regras puras -----------------------------------------------------------

def maior_ofensiva(estudo, protegidos):
    """A maior ofensiva da história, com a regra de `db.contar_ofensiva`: o dia
    protegido não quebra a sequência, mas também não conta."""
    maior = atual = 0
    anterior = None
    for dia in sorted(estudo | protegidos):
        if anterior is None or (dia - anterior).days > 1:
            atual = 0
        if dia in estudo:
            atual += 1
            maior = max(maior, atual)
        anterior = dia
    return maior


def maior_ausencia(estudo):
    """O maior intervalo entre dois dias de estudo, em dias."""
    dias = sorted(estudo)
    return max(((b - a).days for a, b in zip(dias, dias[1:])), default=0)


def maior_sequencia_certa(corretas):
    maior = atual = 0
    for correta in corretas:
        atual = atual + 1 if correta else 0
        maior = max(maior, atual)
    return maior


def trajetoria_da_triagem(tentativas, areas=None):
    """Percorre as primeiras respostas em ordem, `[(area, pontos)]`, e diz o melhor
    momento de cada marco. É um percurso e não uma foto porque "saiu da Emergência" é
    uma história, e o carimbo não pode depender do dia em que a conta foi avaliada.
    Só as cinco grandes áreas, cada uma a partir de RESPOSTAS_MINIMAS_AREA."""
    areas = areas if areas is not None else db.TAXONOMIA
    placar = {}
    em_emergencia = set()
    marcos = {"saiu_emergencia": 0, "areas_verdes_max": 0, "areas_azuis_max": 0, "sem_vermelho": 0}
    for area, pontos in tentativas:
        if area not in areas:
            continue
        total, acertos = placar.get(area, (0, 0.0))
        placar[area] = (total + 1, acertos + float(pontos))
        pcts = {a: 100 * acertos / total for a, (total, acertos) in placar.items() if total >= RESPOSTAS_MINIMAS_AREA}
        if area in pcts:
            if pcts[area] < FAIXA_EMERGENCIA:
                em_emergencia.add(area)
            elif area in em_emergencia:
                marcos["saiu_emergencia"] = 1
        marcos["areas_verdes_max"] = max(marcos["areas_verdes_max"], sum(p >= FAIXA_VERDE for p in pcts.values()))
        marcos["areas_azuis_max"] = max(marcos["areas_azuis_max"], sum(p >= FAIXA_AZUL for p in pcts.values()))
        if len(pcts) == len(areas) and all(p >= FAIXA_EMERGENCIA for p in pcts.values()):
            marcos["sem_vermelho"] = 1
    return marcos


def medidas_de_provas(feitas, pagas, edicoes):
    """`feitas` vem de `db.simulados_oficiais_feitos` e `pagas` são as chaves de prova
    do razão, e a prova só conta se pagou: o XP já exige 90% respondida, e é isso que
    impede de ganhar o carimbo finalizando a prova em branco."""
    validas = []
    for f in feitas:
        if f["em_blocos"]:
            blocos = range(1, db.numero_de_blocos(f["num_questoes"]) + 1)
            if all(progressao.chave_prova(f["banca"], f["edicao"], b) in pagas for b in blocos):
                validas.append(f)
        elif progressao.chave_prova(f["banca"], f["edicao"], None) in pagas:
            validas.append(f)
    bancas = {f["banca"].upper() for f in validas}
    feitas_edicoes = {(f["banca"].upper(), f["edicao"]) for f in validas}
    todas = {(e["banca"].upper(), e["edicao"]) for e in edicoes}
    return {
        "provas": len(feitas_edicoes),
        "provas_em_blocos": sum(1 for f in validas if f["em_blocos"]),
        "prova_acima_corte": int(any(
            f["corte"] and f["corte"]["nota"] is not None and f["corte"]["nota"] >= f["corte"]["corte"] for f in validas
        )),
        "bancas_inep": len(bancas & {"REVALIDA", "ENAMED"}),
        "banca:USP": int("USP" in bancas),
        "banca:UNICAMP": int("UNICAMP" in bancas),
        "provas_pct": 100 * len(feitas_edicoes & todas) // len(todas) if todas else 0,
    }


# --- Leitura do histórico ---------------------------------------------------

def medir(usuario_id):
    """Quanto a conta tem de cada coisa que algum carimbo mede."""
    estudo, protegidos = db.dias_de_ofensiva(usuario_id=usuario_id)
    with get_conn() as conn:
        respostas = conn.execute(
            "SELECT questao_id, correta, substr(respondida_em, 1, 10) AS dia FROM respostas WHERE usuario_id = ? ORDER BY id",
            (usuario_id,),
        ).fetchall()
        tentativas = conn.execute(f"""
            SELECT a.nome AS area, r.pontos FROM ({db._PRIMEIRAS_TENTATIVAS}) r
            JOIN questoes q ON q.id = r.questao_id JOIN areas a ON a.id = q.area_id
            ORDER BY r.id
        """, (usuario_id,)).fetchall()
        eventos = conn.execute(f"""
            SELECT questao_id, origem, {sr._COLUNAS_CLASSIFICACAO} FROM revisao_eventos
            WHERE usuario_id = ? ORDER BY registrado_em, id
        """, (usuario_id,)).fetchall()
        linha = conn.execute("""
            SELECT (SELECT COUNT(*) FROM questoes) AS banco,
                   (SELECT COUNT(*) FROM revisao_cartao_eventos WHERE usuario_id = ?) AS cartoes,
                   (SELECT COUNT(*) FROM relatos_questao WHERE usuario_id = ? AND resolvido_em IS NOT NULL) AS relatos
        """, (usuario_id, usuario_id)).fetchone()
        pagas = {r["chave"] for r in conn.execute(
            "SELECT chave FROM progresso_eventos WHERE usuario_id = ? AND tipo = 'prova'", (usuario_id,),
        ).fetchall()}
        xp_por_area = progressao._xp_por_area(conn, usuario_id)

    medidas = {
        "ofensiva": maior_ofensiva(estudo, protegidos),
        "maior_ausencia": maior_ausencia(estudo),
        "cartoes": linha["cartoes"],
        "relatos_resolvidos": linha["relatos"],
    }

    casos = len({r["questao_id"] for r in respostas})
    por_dia = collections.defaultdict(set)
    for r in respostas:
        por_dia[r["dia"]].add(r["questao_id"])
    medidas.update({
        "casos": casos,
        "banco_pct": 100 * casos // linha["banco"] if linha["banco"] else 0,
        "certos_seguidos": maior_sequencia_certa(r["correta"] for r in respostas),
        "casos_num_dia": max((len(q) for q in por_dia.values()), default=0),
    })

    por_questao = collections.defaultdict(list)
    for e in eventos:
        por_questao[e["questao_id"]].append(e)
    marcas = [m for lista in por_questao.values() for _, m in sr.classificar_eventos(lista)]
    medidas.update({
        "revisoes": sum(1 for e in eventos if e["origem"] == "revisao"),
        "recuperados": sum(1 for m in marcas if m["recuperado"]),
        "consolidados": sum(1 for m in marcas if m["consolidou"]),
    })

    medidas.update(trajetoria_da_triagem((t["area"], t["pontos"]) for t in tentativas))
    projecao = db.nota_projetada(usuario_id=usuario_id) if len(tentativas) >= RESPOSTAS_MINIMAS_PROJECAO else None
    corte = db.corte_de_referencia()
    medidas["acima_corte"] = int(bool(projecao) and projecao["nota"] >= 100 * corte["corte"] / corte["maximo"])

    feitas = db.simulados_oficiais_feitos(usuario_id=usuario_id, limite=1000) if pagas else []
    medidas.update(medidas_de_provas(feitas, pagas, db.listar_edicoes_oficiais() if pagas else []))

    niveis = {area: progressao.progresso_da_area(xp_por_area.get(area, 0))["nivel"] for area in db.TAXONOMIA}
    medidas.update({f"nivel:{area}": nivel for area, nivel in niveis.items()})
    medidas["areas_nivel_10"] = sum(nivel >= 10 for nivel in niveis.values())
    return medidas


# --- Carimbar ---------------------------------------------------------------

def carimbar(conn, usuario_id, medidas, agora):
    """Paga no razão o que as medidas alcançaram, na transação de quem chama. Devolve
    os carimbos novos; a chave única cobre duas avaliações ao mesmo tempo."""
    obtidas = {r["chave"] for r in conn.execute(
        "SELECT chave FROM progresso_eventos WHERE usuario_id = ? AND tipo = 'conquista'", (usuario_id,),
    ).fetchall()}
    novas = []
    for c in CONQUISTAS:
        if chave(c["id"]) in obtidas or medidas.get(c["medida"], 0) < c["alvo"]:
            continue
        pago = progressao._lancar(
            conn, usuario_id=usuario_id, chave=chave(c["id"]), tipo="conquista", xp=0, moedas=c["moedas"],
            area_id=None, agora=agora,
        )
        if pago is not None:
            novas.append({"id": c["id"], "nome": c["nome"], "grau": c["grau"], "moedas": c["moedas"], "obtida_em": agora})
    return novas


def verificar(usuario_id):
    medidas = medir(usuario_id)
    with get_conn() as conn:
        return carimbar(conn, usuario_id, medidas, db.agora_br())


def _obtidas(usuario_id):
    with get_conn() as conn:
        return {
            r["chave"].split(":", 1)[1]: r["criado_em"]
            for r in conn.execute(
                "SELECT chave, criado_em FROM progresso_eventos WHERE usuario_id = ? AND tipo = 'conquista'", (usuario_id,),
            ).fetchall()
        }


def _nota(c, valor):
    if c["nota"]:
        milhar = lambda n: f"{n:,}".replace(",", ".")  # noqa: E731
        return c["nota"].format(v=milhar(min(valor, c["alvo"])), a=milhar(c["alvo"]))
    return c["dica"]


def caderneta(usuario_id):
    """A caderneta inteira. O carimbo secreto ainda não obtido sai sem nome, sem id e
    sem medida: a resposta é o que qualquer curioso lê no navegador."""
    medidas = medir(usuario_id)
    with get_conn() as conn:
        novas = carimbar(conn, usuario_id, medidas, db.agora_br())
    obtidas = _obtidas(usuario_id)

    def publico(c, ordem):
        quando = obtidas.get(c["id"])
        if quando:
            return {"id": c["id"], "nome": c["nome"], "grau": c["grau"], "moedas": c["moedas"],
                    "obtida_em": quando, "nota": None, "pct": None}
        if c["secreta"]:
            return {"id": f"secreta-{ordem}", "nome": "Carimbo secreto", "grau": c["grau"], "moedas": c["moedas"],
                    "obtida_em": None, "nota": "Só aparece quando acontece", "pct": None}
        valor = medidas.get(c["medida"], 0)
        return {"id": c["id"], "nome": c["nome"], "grau": c["grau"], "moedas": c["moedas"], "obtida_em": None,
                "nota": _nota(c, valor), "pct": min(100, 100 * valor / c["alvo"]) if c["nota"] else None}

    series = []
    for nome, carimbos in SERIES:
        itens = [publico(c, i) for i, c in enumerate(carimbos)]
        series.append({"nome": nome, "feitos": sum(1 for i in itens if i["obtida_em"]), "qtd": len(itens), "itens": itens})
    return {"obtidos": len(obtidas), "total": len(CONQUISTAS), "series": series, "novas": novas}


def vitrine(usuario_id, quantos=3):
    """O que o perfil mostra: os de maior grau, e entre eles os mais recentes."""
    obtidas = _obtidas(usuario_id)
    conhecidas = [i for i in obtidas if i in PORTE]
    conhecidas.sort(key=lambda i: (ORDEM_GRAU[PORTE[i]["grau"]], obtidas[i]), reverse=True)
    return {
        "obtidos": len(obtidas),
        "total": len(CONQUISTAS),
        "itens": [{"id": i, "nome": PORTE[i]["nome"], "grau": PORTE[i]["grau"], "obtida_em": obtidas[i]}
                  for i in conhecidas[:quantos]],
    }
