from fastapi import APIRouter, Depends, Query

import db
from api.deps import usuario_atual

router = APIRouter(prefix="/materiais", tags=["materiais"])


@router.get("")
def listar(
    area_id: int | None = None, especialidade_id: int | None = None, subtopico_id: int | None = None,
    tipo: str | None = None, q: str | None = None,
    limite: int = Query(default=50, ge=1, le=200), pagina: int = Query(default=0, ge=0),
    usuario=Depends(usuario_atual),
):
    total = db.contar_materiais_filtrados(area_id, subtopico_id, tipo, q, especialidade_id=especialidade_id)
    itens = db.listar_materiais_paginado(
        area_id, subtopico_id, tipo, q, limite=limite, offset=pagina * limite, especialidade_id=especialidade_id,
    )
    return {"total": total, "itens": itens}


@router.get("/tipos")
def tipos(usuario=Depends(usuario_atual)):
    return db.listar_tipos_materiais()
