from fastapi import APIRouter, Depends, HTTPException, Query, status

import db
import progressao
import repeticao_espacada as sr
from api.deps import usuario_atual
from api.schemas import MarcarRevisaoIn
from api.serialize import questoes_publicas

router = APIRouter(prefix="/revisao", tags=["revisao"])


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
    ids = [q["id"] for q in fila]
    estados = sr.estados_revisao(ids, usuario_id=uid)
    recompensas = progressao.prever_casos(ids, usuario_id=uid)
    proxima = sr.proxima_leva_revisao(usuario_id=uid)
    return {
        "fila": [
            {
                **publica,
                "prazos": sr.prever_prazos(estados.get(publica["id"])),
                "recompensa": recompensas.get(publica["id"]),
            }
            for publica in questoes_publicas(fila)
        ],
        "proxima_leva": proxima,
        "hoje": {
            "meta": plano["meta"],
            "feitas_hoje": plano["feitas_hoje"],
            "excedente": plano["excedente"],
            "segundos_por_caso": plano["segundos_por_caso"],
        },
    }


@router.post("/{questao_id}/avaliar")
def avaliar(questao_id: int, dados: MarcarRevisaoIn, usuario=Depends(usuario_atual)):
    # O cliente reenvia quando não sabe se gravou: avaliar duas vezes empurraria o SM-2.
    if dados.envio and db.envio_ja_registrado(usuario["id"], dados.envio):
        return {"ok": True, "repetido": True, "correta": None, "qualidade": dados.qualidade, "proxima_revisao": None,
                "prazos": None, "recuperado": False, "consolidou": False, "ganho": None}
    try:
        resultado = sr.avaliar_revisao(
            questao_id, dados.qualidade, usuario_id=usuario["id"],
            alternativa=dados.alternativa, tempo_ms=dados.tempo_ms,
        )
    except ValueError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Questão não encontrada.")
    if dados.envio:
        db.registrar_envio(usuario["id"], dados.envio)
    return {
        "ok": True,
        "correta": resultado["correta"],
        "qualidade": resultado["qualidade"],
        "proxima_revisao": resultado["proxima_revisao"],
        "prazos": resultado["prazos"],
        "recuperado": resultado["recuperado"],
        "consolidou": resultado["consolidou"],
        "ganho": resultado["ganho"],
    }
