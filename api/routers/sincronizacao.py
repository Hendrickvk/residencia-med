from fastapi import APIRouter, Depends

import db
from api.deps import usuario_atual

router = APIRouter(prefix="/sincronizacao", tags=["sincronizacao"])


@router.get("")
def status_sincronizacao(usuario=Depends(usuario_atual)):
    """Status é informativo e aparece pra qualquer aluno na tela de
    Materiais — a sincronização em si é tela do Streamlit, só para admin."""
    return {"ultima_sincronizacao": db.ultima_sincronizacao()}
