from fastapi import APIRouter, Depends, HTTPException, status

import conquistas
import progressao
from api.deps import usuario_atual
from api.schemas import EquiparIn

router = APIRouter(prefix="/progresso", tags=["progresso"])


@router.get("")
def obter_progresso(usuario=Depends(usuario_atual)):
    return {**progressao.resumo(usuario), "vitrine": conquistas.vitrine(usuario["id"])}


@router.get("/conquistas")
def obter_conquistas(usuario=Depends(usuario_atual)):
    return conquistas.pagina(usuario["id"])


@router.post("/verificar")
def verificar_conquistas(usuario=Depends(usuario_atual)):
    """O fim da sessão pergunta o que ela conquistou: as moedas entram aqui, uma vez só."""
    return {"novas": conquistas.verificar(usuario["id"])}


@router.get("/loja")
def obter_loja(usuario=Depends(usuario_atual)):
    return progressao.loja(usuario["id"])


@router.post("/loja/{item_id}/comprar")
def comprar(item_id: str, usuario=Depends(usuario_atual)):
    """Devolve a loja inteira de novo: o saldo e o estado de todos os itens mudam."""
    try:
        return progressao.comprar(item_id, usuario_id=usuario["id"])
    except progressao.ItemInexistente:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item não encontrado.")
    except progressao.CompraRecusada as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))


@router.put("/equipar")
def equipar(dados: EquiparIn, usuario=Depends(usuario_atual)):
    try:
        return progressao.equipar(dados.tipo, dados.item, usuario_id=usuario["id"])
    except progressao.ItemInexistente:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item não encontrado.")
    except progressao.CompraRecusada as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
