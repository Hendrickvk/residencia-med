from fastapi import APIRouter, Depends, Query, status

import db
from api.deps import exigir_admin, usuario_atual
from api.schemas import MaterialIn

router = APIRouter(prefix="/materiais", tags=["materiais"])


@router.get("")
def listar(
    area_id: int | None = None, subtopico_id: int | None = None,
    tipo: str | None = None, q: str | None = None,
    limite: int = Query(default=50, ge=1, le=200), pagina: int = Query(default=0, ge=0),
    usuario=Depends(usuario_atual),
):
    total = db.contar_materiais_filtrados(area_id, subtopico_id, tipo, q)
    itens = db.listar_materiais_paginado(area_id, subtopico_id, tipo, q, limite=limite, offset=pagina * limite)
    return {"total": total, "itens": itens}


@router.get("/tipos")
def tipos(usuario=Depends(usuario_atual)):
    return db.listar_tipos_materiais()


@router.post("", status_code=status.HTTP_201_CREATED)
def criar(dados: MaterialIn, usuario=Depends(exigir_admin)):
    db.criar_material(dados.area_id, dados.subtopico_id, dados.tipo, dados.titulo, dados.link)
    return {"ok": True}


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(material_id: int, usuario=Depends(exigir_admin)):
    db.excluir_material(material_id)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def excluir_todos(usuario=Depends(exigir_admin)):
    """Zona de risco: apaga TODOS os materiais do acervo compartilhado."""
    db.excluir_todos_materiais()
