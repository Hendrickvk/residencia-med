from fastapi import APIRouter, Depends

import db
from api.deps import usuario_atual

router = APIRouter(prefix="/areas", tags=["areas"])


@router.get("")
def listar(usuario=Depends(usuario_atual)):
    return db.listar_areas()


@router.get("/{area_id}/especialidades")
def listar_especialidades(area_id: int, usuario=Depends(usuario_atual)):
    return db.listar_especialidades(area_id)
