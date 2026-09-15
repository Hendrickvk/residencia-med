from fastapi import APIRouter, Depends, HTTPException, Response, status

import db
from api.deps import usuario_atual

# Cadastro, edição, importação e imagens de questões são telas do Streamlit
# (app.py), que chama db.py direto — por isso não existem rotas de escrita aqui.
router = APIRouter(prefix="/questoes", tags=["questoes"])


@router.get("/bancas")
def bancas(usuario=Depends(usuario_atual)):
    return db.listar_bancas()


@router.get("/anos")
def anos(usuario=Depends(usuario_atual)):
    return db.listar_anos()


@router.get("/tipos")
def tipos(usuario=Depends(usuario_atual)):
    return list(db.TIPOS_PERGUNTA)


@router.get("/{questao_id}/distribuicao")
def distribuicao(questao_id: int, usuario=Depends(usuario_atual)):
    return db.distribuicao_respostas_questao(questao_id, excluir_usuario_id=usuario["id"])


@router.post("/{questao_id}/marcar")
def marcar(questao_id: int, usuario=Depends(usuario_atual)):
    db.marcar_questao(usuario["id"], questao_id)
    return {"marcada": True}


@router.delete("/{questao_id}/marcar")
def desmarcar(questao_id: int, usuario=Depends(usuario_atual)):
    db.desmarcar_questao(usuario["id"], questao_id)
    return {"marcada": False}


@router.get("/{questao_id}/imagem")
def obter_imagem(questao_id: int, usuario=Depends(usuario_atual)):
    q = db.obter_questao(questao_id)
    if q is None or not q["imagem"]:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sem imagem.")
    return Response(content=bytes(q["imagem"]), media_type=q["imagem_mime"] or "image/png")
