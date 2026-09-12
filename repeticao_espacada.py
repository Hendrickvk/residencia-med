"""
Algoritmo de repetição espaçada (variação simplificada do SM-2).

Cada questão respondida entra numa fila de revisão. A qualidade da
resposta (0 a 5) ajusta o "fator de facilidade" e o intervalo até a
próxima revisão, exatamente como no Anki/SuperMemo.
"""

import datetime
from db import get_conn, listar_questoes_marcadas, questao_esta_marcada, desmarcar_questao


def _agora():
    return datetime.datetime.now()


def obter_estado(questao_id, *, usuario_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM revisao WHERE questao_id = ? AND usuario_id = ?", (questao_id, usuario_id)
        ).fetchone()
        return row


def registrar_revisao(questao_id, qualidade: int, *, usuario_id):
    """
    qualidade: 0-5 (0 = errou feio, 5 = acertou na hora e com confiança)
    Segue o algoritmo SM-2 clássico.
    """
    qualidade = max(0, min(5, qualidade))
    estado = obter_estado(questao_id, usuario_id=usuario_id)

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
        # distinção não existia porque a coluna só guardava data (ver
        # HANDOFF_REDESIGN.md, dívida registrada na Fase 5 do MIGRACAO.md).
        repeticoes = 0
        intervalo = 1
        proxima = _agora() + datetime.timedelta(minutes=10)
    else:
        if repeticoes == 0:
            intervalo = 1
        elif repeticoes == 1:
            intervalo = 6
        else:
            intervalo = round(intervalo * facilidade)
        repeticoes += 1
        proxima = _agora() + datetime.timedelta(days=intervalo)

    facilidade = facilidade + (0.1 - (5 - qualidade) * (0.08 + (5 - qualidade) * 0.02))
    facilidade = max(1.3, facilidade)

    with get_conn() as conn:
        conn.execute("""
            INSERT INTO revisao (usuario_id, questao_id, facilidade, intervalo_dias, repeticoes, proxima_revisao)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (usuario_id, questao_id) DO UPDATE SET
                facilidade = excluded.facilidade,
                intervalo_dias = excluded.intervalo_dias,
                repeticoes = excluded.repeticoes,
                proxima_revisao = excluded.proxima_revisao
        """, (usuario_id, questao_id, facilidade, intervalo, repeticoes, proxima))


def questoes_para_revisar_hoje(*, usuario_id):
    """Nome mantido por compatibilidade (era literal antes da migração pra
    timestamp) — na prática é "vencidas até agora", não "até o fim do dia",
    porque a coluna agora guarda hora exata."""
    with get_conn() as conn:
        return conn.execute("""
            SELECT q.*, r.proxima_revisao, r.repeticoes, r.intervalo_dias
            FROM revisao r
            JOIN questoes q ON q.id = r.questao_id
            WHERE r.usuario_id = ? AND r.proxima_revisao <= ?
            ORDER BY r.proxima_revisao ASC
        """, (usuario_id, _agora())).fetchall()


def questoes_nunca_revisadas(*, usuario_id):
    with get_conn() as conn:
        return conn.execute("""
            SELECT q.* FROM questoes q
            LEFT JOIN revisao r ON r.questao_id = q.id AND r.usuario_id = ?
            WHERE r.questao_id IS NULL
            ORDER BY q.criada_em ASC
        """, (usuario_id,)).fetchall()


def fila_revisao(*, usuario_id):
    """Monta a fila de revisão do dia: pendentes (vencidas) + nunca
    revisadas + marcadas manualmente pelo aluno, com dedup por id — mesma
    lógica que antes só existia montada dentro de app.py (linhas da tela de
    Revisão Espaçada), extraída aqui para não duplicar entre backend e
    qualquer outro consumidor futuro."""
    pendentes = list(questoes_para_revisar_hoje(usuario_id=usuario_id))
    novas = list(questoes_nunca_revisadas(usuario_id=usuario_id))
    marcadas = list(listar_questoes_marcadas(usuario_id=usuario_id))
    ids_ja_incluidos = {q["id"] for q in pendentes + novas}
    marcadas_extra = [q for q in marcadas if q["id"] not in ids_ja_incluidos]
    return pendentes + novas + marcadas_extra


def avaliar_revisao(questao_id, qualidade: int, *, usuario_id):
    """Registra a avaliação no SM-2 e aplica o efeito colateral que
    `app.py` sempre aplicava junto: se a questão estava marcada para
    revisão manual e a resposta não foi 'Errei' (qualidade 1), a marcação é
    removida — a revisão automática do SM-2 assumiu o lugar dela."""
    registrar_revisao(questao_id, qualidade, usuario_id=usuario_id)
    if qualidade != 1 and questao_esta_marcada(usuario_id, questao_id):
        desmarcar_questao(usuario_id, questao_id)


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
