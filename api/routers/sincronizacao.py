from fastapi import APIRouter, Depends, HTTPException, status

import db
import mediafire_import as mf
from api.deps import exigir_admin, usuario_atual
from api.schemas import SincronizacaoIn

router = APIRouter(prefix="/sincronizacao", tags=["sincronizacao"])


@router.get("")
def status_sincronizacao(usuario=Depends(usuario_atual)):
    """Status é informativo e aparece pra qualquer aluno na tela de
    Materiais (`app.py` original nunca escondeu isso atrás de `eh_admin`)
    — só a ação de sincronizar (POST) é restrita."""
    return {"ultima_sincronizacao": db.ultima_sincronizacao()}


@router.post("")
def sincronizar(dados: SincronizacaoIn, usuario=Depends(exigir_admin)):
    """Versão sem progresso ao vivo (decisão registrada em MIGRACAO.md §2):
    o Streamlit atualiza a tela linha a linha via callback; aqui devolvemos
    só o relatório final quando a varredura termina. Se o log ao vivo for
    importante, migrar para SSE/WebSocket depois — não antes, porque esta é
    uma tela administrativa candidata a ficar no Streamlit (MIGRACAO.md §5)."""
    try:
        return mf.sincronizar_pasta_raiz(dados.link_raiz, on_progress=lambda _msg: None)
    except mf.MediaFireError as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(e))
