"""
Algoritmo de repetição espaçada (variação simplificada do SM-2).

Cada questão respondida entra numa fila de revisão. A qualidade da
resposta (0 a 5) ajusta o "fator de facilidade" e o intervalo até a
próxima revisão, exatamente como no Anki/SuperMemo.

`calcular_proximo_estado` é a única implementação do agendamento:
`registrar_revisao` grava o que ela devolve e `prever_prazos` mostra o que
ela devolveria — é isso que garante que o prazo escrito num botão da
Revisão seja o prazo de fato agendado.

Carga do dia (fase 2): a tela de Revisão oferece no máximo a meta diária
do aluno, na ordem de `fila_revisao`; o que passa dela espera. Não há
variação aleatória nos intervalos — quebraria a garantia acima, e a meta
já absorve os picos.

Evolução (fase 3): `revisao_eventos` é lido de volta para mostrar ao aluno
se a memória dele está melhorando — estágios dos casos, retenção por semana
e por especialidade, recuperados e consolidados (`evolucao_memoria`). As
definições moram todas em `classificar_eventos`.
"""

import datetime
import itertools
import statistics

from db import get_conn, listar_questoes_marcadas, obter_questao, questao_esta_marcada, desmarcar_questao

# Nota abaixo de 3 (errou): a questão volta ainda na mesma sessão de estudo.
MINUTOS_APOS_ERRO = 10
# Teto do intervalo (o mesmo padrão do Anki). Sem ele o intervalo multiplica sem
# fim: ~26 acertos seguidos passam do ano 9999 e `datetime` estoura
# (OverflowError), tanto ao gravar quanto ao prever o prazo do botão.
INTERVALO_MAXIMO_DIAS = 36_500
# Notas oferecidas depois de acertar na Revisão: com esforço, lembrei, fácil.
NOTAS_ACERTO = (3, 4, 5)
# Meta diária de casos na Revisão para quem não escolheu outra (usuarios.meta_revisao_diaria).
META_REVISAO_PADRAO = 20
# Sem tempo medido suficiente: ler um caso, responder e ler a discussão.
SEGUNDOS_POR_CASO_PADRAO = 90
# Tempos fora desta faixa não são leitura de um caso: clique de teste (menos de
# 15 s para um enunciado de ~850 caracteres) ou aba esquecida aberta (mais de
# 15 min). Medido em 2026-09-13: das 35 respostas com tempo, 29 tinham menos de
# 15 s, e a mediana crua (5 s) estimava 20 casos em 2 minutos.
_TEMPO_PLAUSIVEL_MS = (15_000, 900_000)
_AMOSTRAS_MINIMAS_TEMPO = 10
# Estágio "consolidado": intervalo de 21 dias ou mais (o corte "mature" do Anki).
# Com o SM-2 daqui, é o 4º acerto seguido (1, 6, 15, 38 dias).
INTERVALO_CONSOLIDADO_DIAS = 21
# Um caso só mede memória quando volta depois de pelo menos 1 dia sem ser visto;
# refazer 10 minutos depois do erro é memória de curto prazo.
DIAS_MINIMOS_TESTE = 1
SEMANAS_EVOLUCAO = 8


def _agora():
    return datetime.datetime.now()


def estados_revisao(questao_ids, *, usuario_id):
    """Estado do SM-2 de várias questões numa consulta só: {questao_id: linha}."""
    ids = list(questao_ids)
    if not ids:
        return {}
    placeholders = ",".join(["?"] * len(ids))
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM revisao WHERE usuario_id = ? AND questao_id IN ({placeholders})",
            [usuario_id] + ids,
        ).fetchall()
    return {r["questao_id"]: r for r in rows}


def calcular_proximo_estado(estado, qualidade: int, agora):
    """SM-2 clássico, sem tocar no banco. `estado` é a linha de `revisao`
    (ou None para questão nunca avaliada); `qualidade` vai de 0 (errou feio)
    a 5 (acertou na hora e com confiança). Devolve o estado depois da
    avaliação, com `proxima_revisao` já calculada a partir de `agora`."""
    qualidade = max(0, min(5, int(qualidade)))

    if estado is None:
        facilidade = 2.5
        intervalo = 1
        repeticoes = 0
    else:
        facilidade = estado["facilidade"]
        intervalo = estado["intervalo_dias"]
        repeticoes = estado["repeticoes"]

    if qualidade < 3:
        # Errou: reinicia o ciclo de repetições. `intervalo_dias` continua
        # valendo 1 (é só o que o próximo acerto vai usar como base — ver
        # ramo `repeticoes == 0` abaixo), mas o AGENDAMENTO real é em 10
        # minutos, não amanhã — antes da migração pra timestamp, essa
        # distinção não existia porque a coluna só guardava data (dívida
        # registrada na Fase 5 do MIGRACAO.md).
        repeticoes = 0
        intervalo = 1
        proxima = agora + datetime.timedelta(minutes=MINUTOS_APOS_ERRO)
    else:
        if repeticoes == 0:
            intervalo = 1
        elif repeticoes == 1:
            intervalo = 6
        else:
            intervalo = min(round(intervalo * facilidade), INTERVALO_MAXIMO_DIAS)
        repeticoes += 1
        proxima = agora + datetime.timedelta(days=intervalo)

    facilidade = facilidade + (0.1 - (5 - qualidade) * (0.08 + (5 - qualidade) * 0.02))
    facilidade = max(1.3, facilidade)

    return {
        "facilidade": facilidade,
        "intervalo_dias": intervalo,
        "repeticoes": repeticoes,
        "proxima_revisao": proxima,
    }


def prever_prazos(estado, notas=(1,) + NOTAS_ACERTO):
    """Prazo que cada nota agendaria se fosse dada agora, para os botões da
    Revisão: {nota: {"minutos": 10}} no erro, {nota: {"dias": 6}} no acerto.
    Sai da mesma conta que `registrar_revisao` grava."""
    agora = _agora()
    prazos = {}
    for nota in notas:
        delta = calcular_proximo_estado(estado, nota, agora)["proxima_revisao"] - agora
        if delta < datetime.timedelta(days=1):
            prazos[nota] = {"minutos": round(delta.total_seconds() / 60)}
        else:
            prazos[nota] = {"dias": delta.days}
    return prazos


def registrar_revisao(questao_id, qualidade: int, *, usuario_id, origem=None, correta=None,
                      alternativa=None, tempo_ms=None):
    """Aplica uma avaliação no SM-2 e grava o evento em `revisao_eventos`, na
    mesma transação. `revisao` guarda só o estado atual (cada avaliação
    sobrescreve a anterior); o evento é o histórico que permite acompanhar a
    retenção do aluno ao longo do tempo.

    `origem`: "pratica", "simulado" ou "revisao" (None nas telas antigas do
    Streamlit). `correta`/`alternativa`: quando houve resposta a uma
    alternativa. Devolve o novo estado."""
    qualidade = max(0, min(5, int(qualidade)))
    agora = _agora()

    with get_conn() as conn:
        estado = conn.execute(
            "SELECT * FROM revisao WHERE questao_id = ? AND usuario_id = ?", (questao_id, usuario_id)
        ).fetchone()
        novo = calcular_proximo_estado(estado, qualidade, agora)

        conn.execute("""
            INSERT INTO revisao (usuario_id, questao_id, facilidade, intervalo_dias, repeticoes, proxima_revisao)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (usuario_id, questao_id) DO UPDATE SET
                facilidade = excluded.facilidade,
                intervalo_dias = excluded.intervalo_dias,
                repeticoes = excluded.repeticoes,
                proxima_revisao = excluded.proxima_revisao
        """, (usuario_id, questao_id, novo["facilidade"], novo["intervalo_dias"],
              novo["repeticoes"], novo["proxima_revisao"]))

        # Atraso em dias em relação ao que estava agendado: positivo = já tinha
        # vencido; negativo = revisada antes (marcada, ou praticada de novo).
        atraso = (agora - estado["proxima_revisao"]).total_seconds() / 86400 if estado else None
        conn.execute("""
            INSERT INTO revisao_eventos (
                usuario_id, questao_id, origem, qualidade, correta, alternativa, tempo_ms,
                facilidade_antes, intervalo_antes, repeticoes_antes, atraso_dias,
                facilidade_depois, intervalo_depois, repeticoes_depois, proxima_revisao, registrado_em
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            usuario_id, questao_id, origem, qualidade,
            None if correta is None else int(bool(correta)), alternativa, tempo_ms,
            estado["facilidade"] if estado else None,
            estado["intervalo_dias"] if estado else None,
            estado["repeticoes"] if estado else None,
            atraso,
            novo["facilidade"], novo["intervalo_dias"], novo["repeticoes"], novo["proxima_revisao"], agora,
        ))

    return novo


def questoes_para_revisar_hoje(*, usuario_id):
    """Nome mantido por compatibilidade (era literal antes da migração pra
    timestamp) — na prática é "vencidas até agora", não "até o fim do dia",
    porque a coluna agora guarda hora exata."""
    with get_conn() as conn:
        return conn.execute("""
            SELECT q.*, a.nome AS area, e.nome AS especialidade,
                   r.proxima_revisao, r.repeticoes, r.intervalo_dias, r.facilidade
            FROM revisao r
            JOIN questoes q ON q.id = r.questao_id
            JOIN areas a ON a.id = q.area_id
            LEFT JOIN especialidades e ON e.id = q.especialidade_id
            WHERE r.usuario_id = ? AND r.proxima_revisao <= ?
            ORDER BY r.proxima_revisao ASC
        """, (usuario_id, _agora())).fetchall()


def _ordenar_por_prioridade(pendentes, marcadas_extra, agora):
    """Ordem da fila, que decide o que entra quando nem tudo cabe na meta:
    1. vencidas em reaprendizado (`repeticoes == 0`: errou e ainda não
       acertou de novo), das mais antigas para as mais novas;
    2. marcadas pelo aluno que não estavam vencidas (pedido explícito);
    3. demais vencidas, da mais atrasada em relação ao próprio intervalo para
       a menos (3 dias de atraso num intervalo de 2 pesam mais que 3 num de
       30) e, empatando, a de menor facilidade primeiro."""
    reaprendendo = sorted((q for q in pendentes if q["repeticoes"] == 0), key=lambda q: q["proxima_revisao"])

    def atraso_relativo(q):
        return (agora - q["proxima_revisao"]).total_seconds() / 86400 / max(q["intervalo_dias"], 1)

    consolidando = sorted(
        (q for q in pendentes if q["repeticoes"] > 0),
        key=lambda q: (-atraso_relativo(q), q["facilidade"]),
    )
    return reaprendendo + list(marcadas_extra) + consolidando


def fila_revisao(*, usuario_id):
    """Todos os candidatos à revisão, em ordem de prioridade
    (`_ordenar_por_prioridade`): vencidas + marcadas pelo aluno, sem repetir.
    A tela não mostra tudo isto: `plano_revisao` corta pela meta diária.

    Questões nunca respondidas NÃO entram. Até 2026-09-13 entravam todas as
    do banco sem registro em `revisao` (regra da primeira versão, com banco
    pequeno); como responder no Praticar/Simulado já agenda a revisão, isso
    enchia a fila com o banco inteiro ainda não visto (591 de 624 itens para
    um aluno com 56 respostas), enquanto a aba contava só as vencidas.
    Questão nova é do Praticar. `contar_fila_revisao` precisa contar
    exatamente o que esta função devolve."""
    agora = _agora()
    pendentes = list(questoes_para_revisar_hoje(usuario_id=usuario_id))
    marcadas = list(listar_questoes_marcadas(usuario_id=usuario_id))
    ids_pendentes = {q["id"] for q in pendentes}
    marcadas_extra = [q for q in marcadas if q["id"] not in ids_pendentes]
    return _ordenar_por_prioridade(pendentes, marcadas_extra, agora)


def contar_fila_revisao(*, usuario_id):
    """Tamanho de `fila_revisao` sem carregar as questões (a contagem da aba e
    do Painel roda a cada carga; as linhas completas trazem até a imagem)."""
    with get_conn() as conn:
        return conn.execute("""
            SELECT COUNT(*) AS total FROM (
                SELECT questao_id FROM revisao WHERE usuario_id = ? AND proxima_revisao <= ?
                UNION
                SELECT questao_id FROM questoes_marcadas WHERE usuario_id = ?
            ) fila
        """, (usuario_id, _agora(), usuario_id)).fetchone()["total"]


def revisadas_hoje(*, usuario_id):
    """Casos distintos avaliados hoje na tela de Revisão — é o que consome a
    meta diária. Praticar e Simulado não contam: são estudo, não revisão. Um
    caso errado e refeito na mesma sessão conta uma vez."""
    inicio_do_dia = _agora().replace(hour=0, minute=0, second=0, microsecond=0)
    with get_conn() as conn:
        return conn.execute("""
            SELECT COUNT(DISTINCT questao_id) AS total FROM revisao_eventos
            WHERE usuario_id = ? AND origem = 'revisao' AND registrado_em >= ?
        """, (usuario_id, inicio_do_dia)).fetchone()["total"]


def segundos_por_caso(*, usuario_id):
    """Tempo típico (mediana) do aluno por caso, para estimar a duração da
    revisão. Usa as revisões dos últimos 60 dias; com poucas medidas, o tempo
    do Praticar; sem nenhum dos dois, SEGUNDOS_POR_CASO_PADRAO. Só entram
    tempos plausíveis (`_TEMPO_PLAUSIVEL_MS`), e a mediana (não a média)
    segura o que ainda escapar."""
    desde = _agora() - datetime.timedelta(days=60)
    minimo, maximo = _TEMPO_PLAUSIVEL_MS
    with get_conn() as conn:
        amostras = [r["tempo_ms"] for r in conn.execute("""
            SELECT tempo_ms FROM revisao_eventos
            WHERE usuario_id = ? AND origem = 'revisao' AND tempo_ms BETWEEN ? AND ? AND registrado_em >= ?
        """, (usuario_id, minimo, maximo, desde)).fetchall()]
        if len(amostras) < _AMOSTRAS_MINIMAS_TEMPO:
            # respostas.respondida_em é TEXT ISO: compara com texto.
            amostras = [r["tempo_ms"] for r in conn.execute("""
                SELECT tempo_ms FROM respostas
                WHERE usuario_id = ? AND tempo_ms BETWEEN ? AND ? AND respondida_em >= ?
            """, (usuario_id, minimo, maximo, desde.isoformat())).fetchall()]
    if len(amostras) < _AMOSTRAS_MINIMAS_TEMPO:
        return SEGUNDOS_POR_CASO_PADRAO
    return round(statistics.median(amostras) / 1000)


def plano_revisao(*, usuario_id, meta, extra=0):
    """O que a tela de Revisão oferece agora: os primeiros candidatos de
    `fila_revisao` que cabem no que falta da meta de hoje. `extra` libera
    mais casos só nesta chamada ("Revisar mais 10"), sem mudar a meta."""
    candidatos = fila_revisao(usuario_id=usuario_id)
    feitas = revisadas_hoje(usuario_id=usuario_id)
    cabem = max(meta - feitas, 0) + max(extra, 0)
    fila = candidatos[:cabem]
    return {
        "fila": fila,
        "meta": meta,
        "feitas_hoje": feitas,
        "excedente": len(candidatos) - len(fila),
        "segundos_por_caso": segundos_por_caso(usuario_id=usuario_id),
    }


def resumo_revisao_hoje(*, usuario_id, meta):
    """Números do dia para a aba e o Painel, sem carregar questões. `hoje` é
    exatamente o tamanho da fila de `plano_revisao` sem `extra`."""
    total = contar_fila_revisao(usuario_id=usuario_id)
    feitas = revisadas_hoje(usuario_id=usuario_id)
    hoje = min(total, max(meta - feitas, 0))
    return {
        "meta": meta,
        "feitas_hoje": feitas,
        "hoje": hoje,
        "excedente": total - hoje,
        "segundos_por_caso": segundos_por_caso(usuario_id=usuario_id),
    }


def previsao_revisoes(*, usuario_id, meta, dias=7):
    """Carga dos próximos `dias` sob a meta, para o aluno ver um pico chegando.
    Cada dia recebe o que vence nele mais o que sobrou do anterior; cabem
    `meta` casos (hoje, só o que ainda falta da meta). Supõe que o aluno
    cumpre a meta todo dia: é previsão de carga, não agendamento.

    Devolve [{"dia": "AAAA-MM-DD", "vencem", "dentro_meta", "acima_meta"}],
    começando por hoje. Hoje, `vencem` inclui o que já venceu e as marcadas."""
    agora = _agora()
    hoje = agora.date()
    fim = datetime.datetime.combine(hoje + datetime.timedelta(days=dias), datetime.time())
    with get_conn() as conn:
        # Marcadas já contam hoje (entram na fila na hora); não contam de novo
        # no dia em que venceriam.
        linhas = conn.execute("""
            SELECT (proxima_revisao::date) AS dia, COUNT(*) AS total FROM revisao
            WHERE usuario_id = ? AND proxima_revisao > ? AND proxima_revisao < ?
              AND questao_id NOT IN (SELECT questao_id FROM questoes_marcadas WHERE usuario_id = ?)
            GROUP BY (proxima_revisao::date)
        """, (usuario_id, agora, fim, usuario_id)).fetchall()
    por_dia = {str(l["dia"])[:10]: l["total"] for l in linhas}

    capacidade_hoje = max(meta - revisadas_hoje(usuario_id=usuario_id), 0)
    sobra = 0
    resultado = []
    for i in range(dias):
        dia = (hoje + datetime.timedelta(days=i)).isoformat()
        vencem = por_dia.get(dia, 0) + (contar_fila_revisao(usuario_id=usuario_id) if i == 0 else 0)
        carga = sobra + vencem
        dentro = min(carga, capacidade_hoje if i == 0 else meta)
        resultado.append({"dia": dia, "vencem": vencem, "dentro_meta": dentro, "acima_meta": carga - dentro})
        sobra = carga - dentro
    return resultado


_COLUNAS_CLASSIFICACAO = "qualidade, correta, repeticoes_antes, intervalo_antes, atraso_dias, intervalo_depois"


def _lembrou(evento):
    if evento["correta"] is not None:
        return bool(evento["correta"])
    return evento["qualidade"] >= 3  # autoavaliação, sem alternativa


def _dias_sem_ver(evento):
    """Dias desde a avaliação anterior do caso (None na primeira). O evento não
    guarda quando ela foi, mas o estado antes diz: um acerto agendou
    `intervalo_antes` dias, um erro (repeticoes 0) agendou MINUTOS_APOS_ERRO,
    e `atraso_dias` é quanto passou do agendado."""
    if evento["repeticoes_antes"] is None:
        return None
    if evento["repeticoes_antes"] >= 1:
        agendado = evento["intervalo_antes"]
    else:
        agendado = MINUTOS_APOS_ERRO / 1440
    return evento["atraso_dias"] + agendado


def classificar_eventos(eventos):
    """Marca os eventos de UMA questão, em ordem cronológica. É a única
    definição dos números da evolução:
    - teste: o caso voltou depois de pelo menos DIAS_MINIMOS_TESTE sem ser
      visto (de qualquer origem). Retenção = testes lembrados / testes;
    - lembrou: acertou pelo gabarito (sem alternativa, nota >= 3);
    - recuperado: o primeiro teste lembrado depois de um erro;
    - consolidou: o intervalo chegou a INTERVALO_CONSOLIDADO_DIAS.
    Devolve [(evento, marcas)]."""
    resultado = []
    devendo = False  # errou e ainda não provou, dias depois, que lembra
    for evento in eventos:
        # Repetições 0 antes = a avaliação anterior foi um erro. Pega também
        # os erros de antes de existir o histórico.
        if evento["repeticoes_antes"] == 0:
            devendo = True
        dias = _dias_sem_ver(evento)
        lembrou = _lembrou(evento)
        teste = dias is not None and dias >= DIAS_MINIMOS_TESTE
        recuperado = teste and lembrou and devendo
        if recuperado:
            devendo = False
        elif not lembrou:
            devendo = True
        consolidou = (
            evento["intervalo_depois"] >= INTERVALO_CONSOLIDADO_DIAS
            and (evento["intervalo_antes"] or 0) < INTERVALO_CONSOLIDADO_DIAS
        )
        resultado.append((evento, {"teste": teste, "lembrou": lembrou, "recuperado": recuperado, "consolidou": consolidou}))
    return resultado


def estagios_casos(*, usuario_id):
    """Casos agendados por estágio, pelo estado atual do SM-2: aprendendo
    (errou por último), consolidando (acertou, intervalo abaixo de
    INTERVALO_CONSOLIDADO_DIAS) e consolidado."""
    with get_conn() as conn:
        linha = conn.execute("""
            SELECT COUNT(*) FILTER (WHERE repeticoes = 0) AS aprendendo,
                   COUNT(*) FILTER (WHERE repeticoes > 0 AND intervalo_dias < ?) AS consolidando,
                   COUNT(*) FILTER (WHERE repeticoes > 0 AND intervalo_dias >= ?) AS consolidado
            FROM revisao WHERE usuario_id = ?
        """, (INTERVALO_CONSOLIDADO_DIAS, INTERVALO_CONSOLIDADO_DIAS, usuario_id)).fetchone()
    return {chave: linha[chave] for chave in ("aprendendo", "consolidando", "consolidado")}


def evolucao_memoria(*, usuario_id, semanas=SEMANAS_EVOLUCAO):
    """Se a memória do aluno está melhorando, para o Painel.

    As semanas são blocos de 7 dias terminando hoje (não semanas do
    calendário): o bloco atual nunca começa vazio numa segunda, e é o mesmo
    período de `ultimos_7_dias`. Por especialidade, as mesmas semanas.

    Devolve {"estagios", "semanas": [{"inicio", "testes", "lembrou"}] do
    bloco mais antigo para o atual, "especialidades": [{"area",
    "especialidade", "testes", "lembrou"}] da menor retenção para a maior,
    "ultimos_7_dias": {"testes", "lembrou", "recuperados", "consolidados",
    "dias_com_revisao"}}."""
    hoje = _agora().date()
    inicio = hoje - datetime.timedelta(days=7 * semanas - 1)
    blocos = [
        {"inicio": (inicio + datetime.timedelta(days=7 * i)).isoformat(), "testes": 0, "lembrou": 0}
        for i in range(semanas)
    ]
    por_especialidade = {}
    recuperados = consolidados = 0
    dias_com_revisao = set()

    with get_conn() as conn:
        # O histórico inteiro das questões avaliadas no período: um recuperado
        # depende de um erro que pode ser anterior a ele.
        eventos = conn.execute("""
            SELECT e.questao_id, e.origem, e.registrado_em, e.qualidade, e.correta, e.repeticoes_antes,
                   e.intervalo_antes, e.atraso_dias, e.intervalo_depois,
                   a.nome AS area, es.nome AS especialidade
            FROM revisao_eventos e
            JOIN questoes q ON q.id = e.questao_id
            JOIN areas a ON a.id = q.area_id
            LEFT JOIN especialidades es ON es.id = q.especialidade_id
            WHERE e.usuario_id = ? AND e.questao_id IN (
                SELECT questao_id FROM revisao_eventos WHERE usuario_id = ? AND registrado_em >= ?
            )
            ORDER BY e.questao_id, e.registrado_em, e.id
        """, (usuario_id, usuario_id, datetime.datetime.combine(inicio, datetime.time()))).fetchall()

    for _, da_questao in itertools.groupby(eventos, key=lambda e: e["questao_id"]):
        for evento, marcas in classificar_eventos(list(da_questao)):
            dia = evento["registrado_em"].date()
            if dia < inicio:
                continue
            bloco = (dia - inicio).days // 7
            if marcas["teste"]:
                blocos[bloco]["testes"] += 1
                blocos[bloco]["lembrou"] += marcas["lembrou"]
                grupo = por_especialidade.setdefault(
                    (evento["area"], evento["especialidade"]),
                    {"area": evento["area"], "especialidade": evento["especialidade"], "testes": 0, "lembrou": 0},
                )
                grupo["testes"] += 1
                grupo["lembrou"] += marcas["lembrou"]
            if bloco == semanas - 1:
                recuperados += marcas["recuperado"]
                consolidados += marcas["consolidou"]
                if evento["origem"] == "revisao":
                    dias_com_revisao.add(dia)

    return {
        "estagios": estagios_casos(usuario_id=usuario_id),
        "semanas": blocos,
        "especialidades": sorted(
            por_especialidade.values(), key=lambda g: (g["lembrou"] / g["testes"], -g["testes"])
        ),
        "ultimos_7_dias": {
            "testes": blocos[-1]["testes"],
            "lembrou": blocos[-1]["lembrou"],
            "recuperados": recuperados,
            "consolidados": consolidados,
            "dias_com_revisao": len(dias_com_revisao),
        },
    }


def avaliar_revisao(questao_id, qualidade: int, *, usuario_id, alternativa=None, tempo_ms=None):
    """Avaliação feita na tela de Revisão.

    Com `alternativa` (o aluno respondeu de novo), quem decide se foi erro é
    o gabarito, não a nota enviada: resposta errada vira nota 1 e resposta
    certa não aceita nota de erro (mínimo 3). Sem `alternativa` (telas
    antigas do Streamlit), vale a nota como veio.

    Mantém o efeito colateral que `app.py` sempre aplicava junto: se a
    questão estava marcada para revisão manual e a nota não foi 1, a
    marcação é removida — a revisão automática do SM-2 assumiu o lugar dela.

    Devolve {"correta", "qualidade", "prazos" (previstos a partir do novo
    estado, para quando o caso reaparece na mesma sessão), "recuperado" e
    "consolidou" (`classificar_eventos`, para o resumo da sessão), + novo
    estado}."""
    correta = None
    if alternativa is not None:
        questao = obter_questao(questao_id)
        if questao is None:
            raise ValueError("Questão não encontrada.")
        correta = alternativa == questao["resposta_correta"]
        qualidade = max(3, int(qualidade)) if correta else 1

    novo = registrar_revisao(
        questao_id, qualidade, usuario_id=usuario_id, origem="revisao",
        correta=correta, alternativa=alternativa, tempo_ms=tempo_ms,
    )
    if qualidade != 1 and questao_esta_marcada(usuario_id, questao_id):
        desmarcar_questao(usuario_id, questao_id)
    with get_conn() as conn:
        historico = conn.execute(f"""
            SELECT {_COLUNAS_CLASSIFICACAO} FROM revisao_eventos
            WHERE usuario_id = ? AND questao_id = ? ORDER BY registrado_em, id
        """, (usuario_id, questao_id)).fetchall()
    marcas = classificar_eventos(historico)[-1][1]
    return {
        "correta": correta, "qualidade": qualidade, "prazos": prever_prazos(novo),
        "recuperado": marcas["recuperado"], "consolidou": marcas["consolidou"], **novo,
    }


def proxima_leva_revisao(*, usuario_id):
    """Primeiro DIA futuro (> agora) com revisões agendadas, e quantas —
    usado no estado vazio da fila ("Nenhuma revisão vencida hoje. As
    próximas 8 vencem na quinta."). Agrupa pela data (não pelo timestamp
    exato) porque itens do mesmo dia têm horários diferentes agora."""
    with get_conn() as conn:
        return conn.execute("""
            SELECT (proxima_revisao::date) AS dia, COUNT(*) AS total
            FROM revisao WHERE usuario_id = ? AND proxima_revisao > ?
            GROUP BY (proxima_revisao::date) ORDER BY dia ASC LIMIT 1
        """, (usuario_id, _agora())).fetchone()
