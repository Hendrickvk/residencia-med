from fastapi import APIRouter, Depends, Query

import db
from api.deps import usuario_atual

router = APIRouter(tags=["busca"])


@router.get("/busca")
def buscar(q: str = Query(min_length=1), usuario=Depends(usuario_atual)):
    return db.busca_global(q)
