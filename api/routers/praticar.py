import random

from fastapi import APIRouter, Depends, HTTPException, Query, status

import db
import repeticao_espacada as sr
from api.deps import usuario_atual
from api.schemas import RespostaIn
from api.serialize import questao_publica

router = APIRouter(tags=["praticar"])


@router.get("/praticar/sessao")
def obter_sessao_pratica(
    area_id: int | None = None,
    subtopico_id: int | None = None,
    banca: str | None = None,
    ano: int | None = None,
    apenas_erros: bool = False,
    excluir_respondidas: bool = False,
    quantidade: int = Query(default=20, ge=1, le=200),
    usuario=Depends(usuario_atual),
):
    """O endpoint que define o sucesso da migração (MIGRACAO.md §0/§2):
    devolve o lote inteiro de questões já com gabarito, comentário e estado
    'marcada' embutidos, para que o cliente nunca precise perguntar nada ao
    servidor entre uma resposta e a próxima."""
    ids = db.ids_questoes_filtro_pratica(
        usuario_id=usuario["id"], area_id=area_id, subtopico_id=subtopico_id,
        banca=banca, ano=ano, apenas_erros=apenas_erros,
        excluir_respondidas=excluir_respondidas,
    )
    random.shuffle(ids)
    ids = ids[:quantidade]
    questoes = db.obter_questoes_por_ids(ids, usuario_id=usuario["id"])
    return {"questoes": [questao_publica(q) for q in questoes]}


@router.post("/respostas")
def registrar_resposta(dados: RespostaIn, usuario=Depends(usuario_atual)):
    """Grava a resposta E aciona o SM-2 na mesma chamada — no app Streamlit
    essas duas escritas sempre acontecem juntas (app.py, `_concluir_pratica`),
    nunca isoladas; tratá-las como endpoints separados quebraria a repetição
    espaçada silenciosamente."""
    q = db.obter_questao(dados.questao_id)
    if q is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Questão não encontrada.")

    correta = dados.alternativa == q["resposta_correta"]
    if correta:
        qualidade = 5 if dados.confianca == "seguro" else 3
    else:
        qualidade = 1

    db.registrar_resposta(
        dados.questao_id, dados.alternativa, correta,
        usuario_id=usuario["id"], confianca=dados.confianca, tempo_ms=dados.tempo_ms,
    )
    sr.registrar_revisao(dados.questao_id, qualidade, usuario_id=usuario["id"])
    return {"correta": correta, "resposta_correta": q["resposta_correta"]}
