from fastapi import APIRouter, Depends, HTTPException, Query, status

import db
import repeticao_espacada as sr
from api.deps import usuario_atual
from api.schemas import RespostaSimuladoIn, SimuladoIn
from api.serialize import questao_publica

router = APIRouter(prefix="/simulados", tags=["simulados"])


def _consolidar_no_historico(simulado_id, usuario_id):
    """Mesma lógica de `app.py::consolidar_simulado_no_historico`: joga as
    respostas do simulado nos mesmos caminhos usados por Praticar, para que
    Painel e revisão espaçada considerem o simulado automaticamente."""
    for item in db.listar_itens_simulado(simulado_id, usuario_id=usuario_id):
        if item["resposta_dada"] is None:
            continue
        correta = bool(item["correta"])
        db.registrar_resposta(item["id"], item["resposta_dada"], correta, usuario_id=usuario_id)
        sr.registrar_revisao(item["id"], 5 if correta else 1, usuario_id=usuario_id)


@router.get("")
def historico(limite: int = Query(default=10, ge=1, le=100), usuario=Depends(usuario_atual)):
    return db.listar_simulados(limite, usuario_id=usuario["id"])


@router.get("/disponiveis")
def disponiveis(area_id: int | None = None, banca: str | None = None, usuario=Depends(usuario_atual)):
    """Declarada antes de `/{simulado_id}` de propósito — senão o FastAPI
    tenta converter 'disponiveis' pra int e devolve 422 em vez de bater
    aqui."""
    return {"total": db.contar_questoes_disponiveis(area_id, banca)}


@router.post("", status_code=status.HTTP_201_CREATED)
def criar(dados: SimuladoIn, usuario=Depends(usuario_atual)):
    disponiveis = db.contar_questoes_disponiveis(dados.area_id, dados.banca)
    if disponiveis < dados.num_questoes:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Só há {disponiveis} questão(ões) disponível(is) para esse filtro.",
        )
    questoes = db.questoes_aleatorias(dados.area_id, dados.banca, limite=dados.num_questoes)
    ids = [q["id"] for q in questoes]
    simulado_id = db.criar_simulado(
        dados.area_id, dados.banca, len(ids), dados.tempo_limite_min, ids, usuario_id=usuario["id"],
    )
    return {"id": simulado_id}


@router.get("/{simulado_id}")
def obter(simulado_id: int, usuario=Depends(usuario_atual)):
    simulado = db.obter_simulado(simulado_id, usuario_id=usuario["id"])
    if simulado is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Simulado não encontrado.")
    return simulado


@router.get("/{simulado_id}/itens")
def itens(simulado_id: int, usuario=Depends(usuario_atual)):
    """Diferente de Praticar: aqui o gabarito NÃO pode viajar pro cliente
    antes de `POST /simulados/{id}/finalizar` — simulado imita uma prova de
    verdade, sem correção por questão. `resposta_correta`/`explicacao` só
    entram no payload depois de finalizado."""
    simulado = db.obter_simulado(simulado_id, usuario_id=usuario["id"])
    if simulado is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Simulado não encontrado.")
    itens = [questao_publica(i) for i in db.listar_itens_simulado(simulado_id, usuario_id=usuario["id"])]
    if simulado["finalizado_em"] is None:
        for item in itens:
            item.pop("resposta_correta", None)
            item.pop("explicacao", None)
    return itens


@router.post("/{simulado_id}/respostas")
def responder(simulado_id: int, dados: RespostaSimuladoIn, usuario=Depends(usuario_atual)):
    try:
        db.registrar_resposta_simulado(simulado_id, dados.questao_id, dados.alternativa, usuario_id=usuario["id"])
    except PermissionError as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(e))
    return {"ok": True}


@router.post("/{simulado_id}/finalizar")
def finalizar(simulado_id: int, usuario=Depends(usuario_atual)):
    try:
        db.finalizar_simulado(simulado_id, usuario_id=usuario["id"])
    except PermissionError as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(e))
    _consolidar_no_historico(simulado_id, usuario["id"])
    return {"ok": True}


@router.get("/{simulado_id}/desempenho")
def desempenho(simulado_id: int, usuario=Depends(usuario_atual)):
    return db.desempenho_simulado(simulado_id, usuario_id=usuario["id"])
