from fastapi import APIRouter, Depends

import db
from api.deps import exigir_admin, usuario_atual
from api.schemas import AreaIn, SubtopicoIn

router = APIRouter(prefix="/areas", tags=["areas"])


@router.get("")
def listar(usuario=Depends(usuario_atual)):
    return db.listar_areas()


@router.post("", status_code=201)
def criar(dados: AreaIn, usuario=Depends(exigir_admin)):
    db.criar_area(dados.nome)
    return {"ok": True}


@router.get("/{area_id}/subtopicos")
def listar_subtopicos(area_id: int, usuario=Depends(usuario_atual)):
    return db.listar_subtopicos(area_id)


@router.post("/{area_id}/subtopicos", status_code=201)
def criar_subtopico(area_id: int, dados: SubtopicoIn, usuario=Depends(exigir_admin)):
    db.criar_subtopico(area_id, dados.nome)
    return {"ok": True}
