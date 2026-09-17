from fastapi import APIRouter, Depends, HTTPException, Response, status

import db
from api.deps import usuario_atual
from api.schemas import RelatoIn

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


@router.get("/partes-relato")
def partes_relato(usuario=Depends(usuario_atual)):
    """Opções do formulário de "Relatar erro" — a lista vive em db.py."""
    return list(db.PARTES_RELATO)


@router.post("/{questao_id}/relato", status_code=status.HTTP_201_CREATED)
def relatar(questao_id: int, dados: RelatoIn, usuario=Depends(usuario_atual)):
    if dados.parte not in db.PARTES_RELATO:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Parte inválida.")
    if db.obter_questao(questao_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Questão não encontrada.")
    relato_id = db.relatar_erro_questao(usuario["id"], questao_id, dados.parte, dados.comentario)
    return {"id": relato_id}


@router.get("/{questao_id}/imagem")
def obter_imagem(questao_id: int, usuario=Depends(usuario_atual)):
    q = db.obter_questao(questao_id)
    if q is None or not q["imagem"]:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sem imagem.")
    return Response(content=bytes(q["imagem"]), media_type=q["imagem_mime"] or "image/png")
