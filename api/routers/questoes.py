import io

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import StreamingResponse

import db
import importador_questoes as imp_q
from api.deps import exigir_admin, usuario_atual
from api.schemas import QuestaoIn
from api.serialize import questao_publica

router = APIRouter(prefix="/questoes", tags=["questoes"])


@router.get("")
def listar_questoes(
    area_id: int | None = None, subtopico_id: int | None = None, q: str | None = None,
    limite: int = Query(default=50, ge=1, le=200), pagina: int = Query(default=0, ge=0),
    usuario=Depends(usuario_atual),
):
    total = db.contar_questoes_filtradas(area_id=area_id, subtopico_id=subtopico_id, busca=q)
    itens = db.listar_questoes_paginado(
        area_id=area_id, subtopico_id=subtopico_id, busca=q,
        limite=limite, offset=pagina * limite,
    )
    return {"total": total, "itens": [questao_publica(i) for i in itens]}


@router.get("/bancas")
def bancas(usuario=Depends(usuario_atual)):
    return db.listar_bancas()


@router.get("/anos")
def anos(usuario=Depends(usuario_atual)):
    return db.listar_anos()


@router.get("/importar/template")
def baixar_template(usuario=Depends(exigir_admin)):
    conteudo = imp_q.gerar_template_bytes()
    return StreamingResponse(
        io.BytesIO(conteudo),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=modelo_importacao_questoes.xlsx"},
    )


@router.post("/importar")
async def importar_planilha(arquivo: UploadFile, usuario=Depends(exigir_admin)):
    try:
        df = imp_q.ler_planilha(io.BytesIO(await arquivo.read()), arquivo.filename)
    except Exception as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Não consegui ler o arquivo: {e}")
    faltando = imp_q.validar_planilha(df)
    if faltando:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Faltam colunas obrigatórias: {', '.join(faltando)}")
    return imp_q.importar(df)


@router.get("/{questao_id}")
def obter_questao(questao_id: int, usuario=Depends(usuario_atual)):
    q = db.obter_questao(questao_id)
    if q is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Questão não encontrada.")
    return questao_publica(q)


@router.post("", status_code=status.HTTP_201_CREATED)
def criar_questao(dados: QuestaoIn, usuario=Depends(exigir_admin)):
    db.criar_questao(
        dados.area_id, dados.subtopico_id, dados.enunciado, dados.alternativas,
        dados.resposta_correta, dados.explicacao, dados.banca, dados.ano,
    )
    return {"ok": True}


@router.put("/{questao_id}")
def atualizar_questao(questao_id: int, dados: QuestaoIn, usuario=Depends(exigir_admin)):
    if db.obter_questao(questao_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Questão não encontrada.")
    db.atualizar_questao(
        questao_id, dados.area_id, dados.subtopico_id, dados.enunciado, dados.alternativas,
        dados.resposta_correta, dados.explicacao, dados.banca, dados.ano,
    )
    return {"ok": True}


@router.delete("/{questao_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_questao(questao_id: int, usuario=Depends(exigir_admin)):
    db.excluir_questao(questao_id)


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


@router.post("/{questao_id}/imagem")
async def definir_imagem(questao_id: int, arquivo: UploadFile, usuario=Depends(exigir_admin)):
    db.definir_imagem_questao(questao_id, await arquivo.read(), arquivo.content_type)
    return {"ok": True}


@router.delete("/{questao_id}/imagem")
def remover_imagem(questao_id: int, usuario=Depends(exigir_admin)):
    db.remover_imagem_questao(questao_id)
    return {"ok": True}
