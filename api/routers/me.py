from fastapi import APIRouter, Depends

import db
from api.deps import eh_admin, usuario_atual
from api.schemas import MeOut, ProvaAlvoIn, TemaIn

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=MeOut)
def obter_me(usuario=Depends(usuario_atual)):
    ofensiva_dias, respondeu_hoje = db.calcular_ofensiva(usuario_id=usuario["id"])
    return MeOut(
        id=usuario["id"],
        email=usuario["email"],
        is_admin=eh_admin(usuario),
        tema=usuario["tema"],
        prova_alvo=usuario["data_prova_alvo"],
        ofensiva_dias=ofensiva_dias,
        respondeu_hoje=respondeu_hoje,
        respondidas_hoje=db.contar_respondidas_hoje(usuario_id=usuario["id"]),
        total_questoes=db.contar_questoes(),
        total_materiais=db.contar_materiais(),
    )


@router.patch("/tema")
def atualizar_tema(dados: TemaIn, usuario=Depends(usuario_atual)):
    db.atualizar_tema_usuario(usuario["id"], dados.tema)
    return {"tema": dados.tema}


@router.patch("/prova-alvo")
def atualizar_prova_alvo(dados: ProvaAlvoIn, usuario=Depends(usuario_atual)):
    data_iso = dados.data.isoformat() if dados.data else None
    db.definir_prova_alvo(usuario["id"], data_iso)
    return {"prova_alvo": data_iso}
