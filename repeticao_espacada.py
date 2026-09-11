"""
Algoritmo de repetição espaçada (variação simplificada do SM-2).

Cada questão respondida entra numa fila de revisão. A qualidade da
resposta (0 a 5) ajusta o "fator de facilidade" e o intervalo até a
próxima revisão, exatamente como no Anki/SuperMemo.
"""

import datetime
from db import get_conn


def _hoje():
    return datetime.date.today()


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
        # errou: reinicia o ciclo de repetições, revisa amanhã
        repeticoes = 0
        intervalo = 1
    else:
        if repeticoes == 0:
            intervalo = 1
        elif repeticoes == 1:
            intervalo = 6
        else:
            intervalo = round(intervalo * facilidade)
        repeticoes += 1

    facilidade = facilidade + (0.1 - (5 - qualidade) * (0.08 + (5 - qualidade) * 0.02))
    facilidade = max(1.3, facilidade)

    proxima = _hoje() + datetime.timedelta(days=intervalo)

    with get_conn() as conn:
        conn.execute("""
            INSERT INTO revisao (usuario_id, questao_id, facilidade, intervalo_dias, repeticoes, proxima_revisao)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (usuario_id, questao_id) DO UPDATE SET
                facilidade = excluded.facilidade,
                intervalo_dias = excluded.intervalo_dias,
                repeticoes = excluded.repeticoes,
                proxima_revisao = excluded.proxima_revisao
        """, (usuario_id, questao_id, facilidade, intervalo, repeticoes, proxima.isoformat()))


def questoes_para_revisar_hoje(*, usuario_id):
    with get_conn() as conn:
        return conn.execute("""
            SELECT q.*, r.proxima_revisao, r.repeticoes, r.intervalo_dias
            FROM revisao r
            JOIN questoes q ON q.id = r.questao_id
            WHERE r.usuario_id = ? AND r.proxima_revisao <= ?
            ORDER BY r.proxima_revisao ASC
        """, (usuario_id, _hoje().isoformat())).fetchall()


def questoes_nunca_revisadas(*, usuario_id):
    with get_conn() as conn:
        return conn.execute("""
            SELECT q.* FROM questoes q
            LEFT JOIN revisao r ON r.questao_id = q.id AND r.usuario_id = ?
            WHERE r.questao_id IS NULL
            ORDER BY q.criada_em ASC
        """, (usuario_id,)).fetchall()


def proxima_leva_revisao(*, usuario_id):
    """Primeira data futura (> hoje) com revisões agendadas, e quantas —
    usado no estado vazio da fila ("Nenhuma revisão vencida hoje. As
    próximas 8 vencem na quinta.")."""
    with get_conn() as conn:
        return conn.execute("""
            SELECT proxima_revisao AS dia, COUNT(*) AS total
            FROM revisao WHERE usuario_id = ? AND proxima_revisao > ?
            GROUP BY proxima_revisao ORDER BY proxima_revisao ASC LIMIT 1
        """, (usuario_id, _hoje().isoformat())).fetchone()
