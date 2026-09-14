from fastapi import APIRouter, Depends, HTTPException, Query, status

import repeticao_espacada as sr
from api.deps import usuario_atual
from api.schemas import MarcarRevisaoIn
from api.serialize import questao_publica

router = APIRouter(prefix="/revisao", tags=["revisao"])


def _prazos_json(prazos):
    # Chaves de dict em JSON são texto: {"1": {"minutos": 10}, "4": {"dias": 6}}.
    return {str(nota): prazo for nota, prazo in prazos.items()}


@router.get("/leva")
def obter_leva(
    extra: int = Query(default=0, ge=0, le=200, description="Casos além da meta de hoje ('Revisar mais 10')."),
    usuario=Depends(usuario_atual),
):
    uid = usuario["id"]
    plano = sr.plano_revisao(usuario_id=uid, meta=usuario["meta_revisao_diaria"], extra=extra)
    fila = plano["fila"]
    # Uma consulta para o estado de todas; o prazo de cada botão sai do mesmo
    # cálculo que agenda (repeticao_espacada.prever_prazos).
    estados = sr.estados_revisao([q["id"] for q in fila], usuario_id=uid)
    proxima = sr.proxima_leva_revisao(usuario_id=uid)
    return {
        "fila": [
            {**questao_publica(q), "prazos": _prazos_json(sr.prever_prazos(estados.get(q["id"])))}
            for q in fila
        ],
        "proxima_leva": {"dia": proxima["dia"], "total": proxima["total"]} if proxima else None,
        "hoje": {
            "meta": plano["meta"],
            "feitas_hoje": plano["feitas_hoje"],
            "excedente": plano["excedente"],
            "segundos_por_caso": plano["segundos_por_caso"],
        },
    }


@router.post("/{questao_id}/avaliar")
def avaliar(questao_id: int, dados: MarcarRevisaoIn, usuario=Depends(usuario_atual)):
    try:
        resultado = sr.avaliar_revisao(
            questao_id, dados.qualidade, usuario_id=usuario["id"],
            alternativa=dados.alternativa, tempo_ms=dados.tempo_ms,
        )
    except ValueError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Questão não encontrada.")
    return {
        "ok": True,
        "correta": resultado["correta"],
        "qualidade": resultado["qualidade"],
        "proxima_revisao": resultado["proxima_revisao"],
        "prazos": _prazos_json(resultado["prazos"]),
        "recuperado": resultado["recuperado"],
        "consolidou": resultado["consolidou"],
    }
