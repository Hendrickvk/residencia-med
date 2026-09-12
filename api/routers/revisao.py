from fastapi import APIRouter, Depends

import repeticao_espacada as sr
from api.deps import usuario_atual
from api.schemas import MarcarRevisaoIn
from api.serialize import questao_publica

router = APIRouter(prefix="/revisao", tags=["revisao"])


@router.get("/leva")
def obter_leva(usuario=Depends(usuario_atual)):
    fila = sr.fila_revisao(usuario_id=usuario["id"])
    proxima = sr.proxima_leva_revisao(usuario_id=usuario["id"])
    return {
        "fila": [questao_publica(q) for q in fila],
        "proxima_leva": {"dia": proxima["dia"], "total": proxima["total"]} if proxima else None,
    }


@router.post("/{questao_id}/avaliar")
def avaliar(questao_id: int, dados: MarcarRevisaoIn, usuario=Depends(usuario_atual)):
    sr.avaliar_revisao(questao_id, dados.qualidade, usuario_id=usuario["id"])
    return {"ok": True}
