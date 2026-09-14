"""
Dá à conta demo um histórico de revisão espaçada, para a Evolução da memória
(fase 3) e a carga da Revisão (fase 2) aparecerem na demonstração.

As respostas semeadas por seed_demo_user.py passam, em ordem, pelo SM-2 real
(`repeticao_espacada.calcular_proximo_estado`, com as notas do Praticar:
seguro 5, chute 3, erro 1). Por cima delas, sessões de Revisão sintéticas às
21h em cerca de 9 de cada 10 dias, na ordem de prioridade e dentro da meta
diária (`_ordenar_por_prioridade`; META_DEMO, gravada na demo), mais um
"Revisar mais 10" quando sobra pelo menos um lote além da meta; caso errado
volta alguns casos adiante, como na tela. Na primeira versão (20 por dia, 3 dias
pulados em cada 10) a fila da demo acumulou e a previsão de 7 dias ficou toda
acima da meta — a imagem oposta à da fase 2. A chance de lembrar parte da taxa de
acerto da área na demo e sobe devagar até hoje, para a evolução ter o que
mostrar. `respostas` não muda: o quadro de triagem da demo fica igual.

Uma transação só; sem --aplicar, desfaz no fim e só mostra o resumo:
    python scripts/seed_demo_revisao.py            # simula
    python scripts/seed_demo_revisao.py --aplicar  # grava
    python scripts/seed_demo_revisao.py --refazer --aplicar

Idempotente: se a demo já tiver qualquer linha em `revisao` ou
`revisao_eventos`, não faz nada — a não ser com --refazer, que salva essas
linhas em backups/ (JSON, fora do git) e as apaga na mesma transação antes de
gerar de novo. Só a conta demo é tocada.
"""

import argparse
import datetime
import itertools
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import db  # noqa: E402
import repeticao_espacada as sr  # noqa: E402

EMAIL_DEMO = "demo@residenciamed.com"
HORA_SESSAO = 21
CHANCE_DE_PULAR_O_DIA = 0.1
LOTE_EXTRA = 10  # o "Revisar mais 10" da tela
# Gravada em usuarios.meta_revisao_diaria da demo. Com ~200 casos quase todos
# consolidando, a carga é de ~30 por dia: com a meta padrão (20) a previsão
# ficava acima da meta em 4 dos 7 dias mesmo revisando quase todo dia.
META_DEMO = 30
SEMENTE = 2026  # mesmo histórico a cada simulação
PASTA_BACKUP = Path(__file__).resolve().parent.parent / "backups"

COLUNAS_EVENTO = (
    "usuario_id", "questao_id", "origem", "qualidade", "correta", "alternativa", "tempo_ms",
    "facilidade_antes", "intervalo_antes", "repeticoes_antes", "atraso_dias",
    "facilidade_depois", "intervalo_depois", "repeticoes_depois", "proxima_revisao", "registrado_em",
)


class _SoSimulacao(Exception):
    """Levantada dentro da transação para desfazê-la (get_conn faz rollback)."""


def _chance_de_lembrar(taxa_area, estado, progresso, refeito):
    if refeito:
        return 0.85  # acabou de ler a discussão do erro
    chance = 0.30 + 0.5 * taxa_area + 0.15 * progresso
    if estado["repeticoes"] == 0:
        chance -= 0.08
    elif estado["repeticoes"] >= 2:
        chance += 0.08
    return min(max(chance, 0.2), 0.95)


def _inserir_em_lotes(conn, tabela, colunas, linhas, tamanho=200):
    grupo = "(" + ", ".join(["?"] * len(colunas)) + ")"
    for inicio in range(0, len(linhas), tamanho):
        lote = linhas[inicio:inicio + tamanho]
        conn.execute(
            f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES {', '.join([grupo] * len(lote))}",
            [valor for linha in lote for valor in linha],
        )


def _resumo_semanal(eventos, hoje, semanas=sr.SEMANAS_EVOLUCAO):
    inicio = hoje - datetime.timedelta(days=7 * semanas - 1)
    blocos = [[0, 0] for _ in range(semanas)]
    ordenados = sorted(eventos, key=lambda e: (e["questao_id"], e["registrado_em"]))
    for _, da_questao in itertools.groupby(ordenados, key=lambda e: e["questao_id"]):
        for evento, marcas in sr.classificar_eventos(list(da_questao)):
            dia = evento["registrado_em"].date()
            if dia >= inicio and marcas["teste"]:
                bloco = blocos[(dia - inicio).days // 7]
                bloco[0] += 1
                bloco[1] += marcas["lembrou"]
    return blocos


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--aplicar", action="store_true", help="grava de verdade (sem isto, desfaz no fim)")
    parser.add_argument("--refazer", action="store_true", help="salva em backups/ e apaga o histórico de revisão da demo antes")
    args = parser.parse_args()
    aplicar, refazer = args.aplicar, args.refazer
    rng = random.Random(SEMENTE)

    usuario = db.obter_usuario_por_email(EMAIL_DEMO)
    if not usuario:
        print("Conta demo não existe: rode scripts/seed_demo_user.py antes.")
        return
    uid = usuario["id"]

    with db.get_conn() as conn:
        ja_tem = conn.execute("""
            SELECT (SELECT COUNT(*) FROM revisao WHERE usuario_id = ?)
                 + (SELECT COUNT(*) FROM revisao_eventos WHERE usuario_id = ?) AS n
        """, (uid, uid)).fetchone()["n"]
        respostas = conn.execute("""
            SELECT r.questao_id, r.resposta_dada, r.correta, r.respondida_em, r.confianca,
                   q.area_id, q.resposta_correta, q.alternativas
            FROM respostas r JOIN questoes q ON q.id = r.questao_id
            WHERE r.usuario_id = ? ORDER BY r.respondida_em
        """, (uid,)).fetchall()
    if ja_tem and not refazer:
        print(f"Conta demo já tem {ja_tem} linha(s) de revisão: nada a fazer (--refazer para gerar de novo).")
        return
    if not respostas:
        print("Conta demo sem respostas: rode scripts/seed_demo_user.py antes.")
        return

    questoes = {r["questao_id"]: r for r in respostas}
    taxa_area = {}
    for area_id, grupo in itertools.groupby(sorted(respostas, key=lambda r: r["area_id"]), key=lambda r: r["area_id"]):
        grupo = list(grupo)
        taxa_area[area_id] = sum(r["correta"] for r in grupo) / len(grupo)

    agora = datetime.datetime.now()
    marcos = [(datetime.datetime.fromisoformat(r["respondida_em"]), 0, r) for r in respostas]
    primeiro_dia = marcos[0][0].date()
    dia = primeiro_dia
    while dia <= agora.date():
        momento = datetime.datetime.combine(dia, datetime.time(HORA_SESSAO, rng.randint(0, 40)))
        if momento < agora and rng.random() > CHANCE_DE_PULAR_O_DIA:
            marcos.append((momento, 1, None))
        dia += datetime.timedelta(days=1)
    marcos.sort(key=lambda m: (m[0], m[1]))
    duracao_total = (agora - marcos[0][0]).total_seconds()

    estados = {}
    eventos = []

    def avaliar(questao_id, qualidade, momento, origem, correta, alternativa, tempo_ms):
        estado = estados.get(questao_id)
        novo = sr.calcular_proximo_estado(estado, qualidade, momento)
        eventos.append({
            "usuario_id": uid, "questao_id": questao_id, "origem": origem, "qualidade": qualidade,
            "correta": int(correta), "alternativa": alternativa, "tempo_ms": tempo_ms,
            "facilidade_antes": estado["facilidade"] if estado else None,
            "intervalo_antes": estado["intervalo_dias"] if estado else None,
            "repeticoes_antes": estado["repeticoes"] if estado else None,
            "atraso_dias": (momento - estado["proxima_revisao"]).total_seconds() / 86400 if estado else None,
            "facilidade_depois": novo["facilidade"], "intervalo_depois": novo["intervalo_dias"],
            "repeticoes_depois": novo["repeticoes"], "proxima_revisao": novo["proxima_revisao"],
            "registrado_em": momento,
        })
        estados[questao_id] = novo

    for momento, tipo, resposta in marcos:
        if tipo == 0:
            qualidade = (5 if resposta["confianca"] == "seguro" else 3) if resposta["correta"] else 1
            avaliar(resposta["questao_id"], qualidade, momento, "pratica",
                    resposta["correta"], resposta["resposta_dada"], None)
            continue

        progresso = (momento - marcos[0][0]).total_seconds() / duracao_total
        pendentes = [{"id": qid, **estado} for qid, estado in estados.items() if estado["proxima_revisao"] <= momento]
        candidatos = [q["id"] for q in sr._ordenar_por_prioridade(pendentes, [], momento)]
        fila = candidatos[:META_DEMO + (LOTE_EXTRA if len(candidatos) - META_DEMO >= LOTE_EXTRA else 0)]
        relogio, refeitos, i = momento, set(), 0
        while i < len(fila):
            qid = fila[i]
            questao = questoes[qid]
            lembrou = rng.random() < _chance_de_lembrar(taxa_area[questao["area_id"]], estados[qid], progresso, qid in refeitos)
            tempo_ms = int(rng.uniform(40, 150) * 1000)
            relogio += datetime.timedelta(milliseconds=tempo_ms)
            if lembrou:
                nota, alternativa = rng.choices([3, 4, 5], weights=[3, 5, 2])[0], questao["resposta_correta"]
            else:
                letras = json.loads(questao["alternativas"]) if isinstance(questao["alternativas"], str) else questao["alternativas"]
                nota = 1
                alternativa = rng.choice([l for l in letras if l != questao["resposta_correta"]] or list(letras))
            avaliar(qid, nota, relogio, "revisao", lembrou, alternativa, tempo_ms)
            if not lembrou and qid not in refeitos:
                fila.insert(min(i + 4, len(fila)), qid)  # volta alguns casos adiante, uma vez
                refeitos.add(qid)
            i += 1

    por_origem = {o: sum(1 for e in eventos if e["origem"] == o) for o in ("pratica", "revisao")}
    estagios = {
        "aprendendo": sum(1 for e in estados.values() if e["repeticoes"] == 0),
        "consolidando": sum(1 for e in estados.values() if e["repeticoes"] > 0 and e["intervalo_dias"] < sr.INTERVALO_CONSOLIDADO_DIAS),
        "consolidado": sum(1 for e in estados.values() if e["repeticoes"] > 0 and e["intervalo_dias"] >= sr.INTERVALO_CONSOLIDADO_DIAS),
    }
    print(f"Conta demo (id {uid}): {len(respostas)} respostas de {primeiro_dia} a {marcos[-1][0].date()}")
    print(f"Eventos: {por_origem['pratica']} do Praticar, {por_origem['revisao']} da Revisão "
          f"em {sum(1 for m in marcos if m[1] == 1)} sessões; {len(estados)} casos em `revisao`")
    print(f"Estágios: {estagios}")
    # Mesma ideia de repeticao_espacada.previsao_revisoes: o que passa da meta vai para o dia seguinte.
    carga, sobra = [], 0
    for i in range(7):
        dia = agora.date() + datetime.timedelta(days=i)
        vencem = sum(
            1 for e in estados.values()
            if (e["proxima_revisao"].date() <= dia if i == 0 else e["proxima_revisao"].date() == dia)
        )
        carga.append(sobra + vencem)
        sobra = max(sobra + vencem - META_DEMO, 0)
    print(f"Carga dos próximos 7 dias (meta {META_DEMO}): {carga}")
    print("Retenção por bloco de 7 dias (testes, lembrou, %):")
    for testes, lembrou in _resumo_semanal(eventos, agora.date()):
        print(f"  {testes:4d} {lembrou:4d} {f'{100 * lembrou / testes:.0f}%' if testes else '-':>5}")

    try:
        with db.get_conn() as conn:
            if ja_tem:  # só chega aqui com --refazer
                antigos = {
                    tabela: [dict(l) for l in conn.execute(f"SELECT * FROM {tabela} WHERE usuario_id = ?", (uid,)).fetchall()]
                    for tabela in ("revisao", "revisao_eventos")
                }
                antigos["meta_revisao_diaria"] = usuario["meta_revisao_diaria"]
                if aplicar:
                    PASTA_BACKUP.mkdir(exist_ok=True)
                    caminho = PASTA_BACKUP / f"demo_revisao_{agora:%Y%m%d_%H%M%S}.json"
                    caminho.write_text(json.dumps(antigos, ensure_ascii=False, default=str), encoding="utf-8")
                    print(f"Backup: {caminho} ({len(antigos['revisao'])} + {len(antigos['revisao_eventos'])} linhas)")
                conn.execute("DELETE FROM revisao_eventos WHERE usuario_id = ?", (uid,))
                conn.execute("DELETE FROM revisao WHERE usuario_id = ?", (uid,))
            conn.execute("UPDATE usuarios SET meta_revisao_diaria = ? WHERE id = ?", (META_DEMO, uid))
            _inserir_em_lotes(conn, "revisao_eventos", COLUNAS_EVENTO, [[e[c] for c in COLUNAS_EVENTO] for e in eventos])
            _inserir_em_lotes(
                conn, "revisao",
                ("usuario_id", "questao_id", "facilidade", "intervalo_dias", "repeticoes", "proxima_revisao"),
                [[uid, qid, e["facilidade"], e["intervalo_dias"], e["repeticoes"], e["proxima_revisao"]] for qid, e in estados.items()],
            )
            if not aplicar:
                raise _SoSimulacao
    except _SoSimulacao:
        print("Simulação: inserções testadas e desfeitas. Rode com --aplicar para gravar.")
        return

    memoria = sr.evolucao_memoria(usuario_id=uid)
    print("Gravado. Evolução da memória lida do banco:")
    print(json.dumps(memoria, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
