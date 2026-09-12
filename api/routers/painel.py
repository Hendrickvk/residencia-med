from fastapi import APIRouter, Depends

import db
import repeticao_espacada as sr
from api.deps import usuario_atual

router = APIRouter(prefix="/painel", tags=["painel"])


@router.get("")
def obter_painel(usuario=Depends(usuario_atual)):
    uid = usuario["id"]
    dash = db.desempenho_dashboard_combinado(usuario_id=uid)
    evolucao = db.evolucao_diaria(usuario_id=uid)
    revisoes_hoje = sr.questoes_para_revisar_hoje(usuario_id=uid)

    por_area = dash["por_area"]
    total_respostas = sum(r["total"] for r in por_area)
    total_acertos = sum(r["acertos"] for r in por_area)
    pct_geral = round(100 * total_acertos / total_respostas, 1) if total_respostas else 0.0

    return {
        "totais": {
            "respostas": total_respostas,
            "acertos": total_acertos,
            "pct_acerto_geral": pct_geral,
        },
        "por_area": por_area,
        "por_banca": dash["por_banca"],
        "evolucao_14_dias": evolucao[-14:] if evolucao else [],
        "respondidas_hoje": db.contar_respondidas_hoje(usuario_id=uid),
        "revisoes_hoje": len(revisoes_hoje),
    }
