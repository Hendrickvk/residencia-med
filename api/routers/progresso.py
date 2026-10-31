from fastapi import APIRouter, Depends

import progressao
from api.deps import usuario_atual

router = APIRouter(prefix="/progresso", tags=["progresso"])


@router.get("")
def obter_progresso(usuario=Depends(usuario_atual)):
    return progressao.resumo(usuario)
