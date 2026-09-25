from fastapi import APIRouter, Depends, HTTPException, Query, status

import db
import repeticao_espacada as sr
from api.deps import usuario_atual
from api.schemas import BaralhoIn, CartaoIn, NotaCartaoIn, PastaIn

router = APIRouter(prefix="/cartoes", tags=["cartoes"])

# Flashcards escritos pela própria aluna. Tudo aqui é dela: **toda** consulta
# leva o `usuario_id` para dentro do WHERE (nas funções do `db`), que é o que
# impede pedir a pasta de outra pessoa mandando o id dela — mesma regra que os
# endpoints de simulado já seguem.
#
# O SM-2 é o mesmo das questões (`repeticao_espacada`); este router não
# calcula intervalo nenhum.


@router.get("/pastas")
def listar_pastas(usuario=Depends(usuario_atual)):
    return {"pastas": db.listar_pastas(usuario_id=usuario["id"])}


@router.post("/pastas", status_code=status.HTTP_201_CREATED)
def criar_pasta(dados: PastaIn, usuario=Depends(usuario_atual)):
    return {"id": db.criar_pasta(usuario_id=usuario["id"], nome=dados.nome, cor=dados.cor)}


@router.patch("/pastas/{pasta_id}")
def atualizar_pasta(pasta_id: int, dados: PastaIn, usuario=Depends(usuario_atual)):
    db.atualizar_pasta(pasta_id, usuario_id=usuario["id"], nome=dados.nome, cor=dados.cor)
    return {"ok": True}


@router.delete("/pastas/{pasta_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_pasta(pasta_id: int, usuario=Depends(usuario_atual)):
    """Leva junto os baralhos e os cartões da pasta. Quem avisa disso é a
    tela — aqui não há como desfazer."""
    db.excluir_pasta(pasta_id, usuario_id=usuario["id"])


@router.post("/baralhos", status_code=status.HTTP_201_CREATED)
def criar_baralho(dados: BaralhoIn, usuario=Depends(usuario_atual)):
    baralho_id = db.criar_baralho(usuario_id=usuario["id"], pasta_id=dados.pasta_id, nome=dados.nome)
    if baralho_id is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pasta não encontrada.")
    return {"id": baralho_id}


@router.get("/baralhos/{baralho_id}")
def obter_baralho(baralho_id: int, usuario=Depends(usuario_atual)):
    baralho = db.obter_baralho(baralho_id, usuario_id=usuario["id"])
    if baralho is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Baralho não encontrado.")
    return {
        "baralho": dict(baralho),
        "cartoes": [dict(c) for c in db.listar_cartoes(baralho_id, usuario_id=usuario["id"])],
    }


@router.patch("/baralhos/{baralho_id}")
def atualizar_baralho(baralho_id: int, dados: BaralhoIn, usuario=Depends(usuario_atual)):
    db.atualizar_baralho(baralho_id, usuario_id=usuario["id"], nome=dados.nome, pasta_id=dados.pasta_id)
    return {"ok": True}


@router.delete("/baralhos/{baralho_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_baralho(baralho_id: int, usuario=Depends(usuario_atual)):
    db.excluir_baralho(baralho_id, usuario_id=usuario["id"])


@router.post("", status_code=status.HTTP_201_CREATED)
def criar_cartao(dados: CartaoIn, usuario=Depends(usuario_atual)):
    if dados.baralho_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Informe o baralho.")
    cartao_id = db.criar_cartao(
        usuario_id=usuario["id"], baralho_id=dados.baralho_id,
        frente=dados.frente, verso=dados.verso, questao_id=dados.questao_id,
    )
    if cartao_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Baralho não encontrado, ou cartão em branco.")
    return {"id": cartao_id}


@router.patch("/{cartao_id}")
def atualizar_cartao(cartao_id: int, dados: CartaoIn, usuario=Depends(usuario_atual)):
    db.atualizar_cartao(cartao_id, usuario_id=usuario["id"], frente=dados.frente, verso=dados.verso)
    return {"ok": True}


@router.delete("/{cartao_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_cartao(cartao_id: int, usuario=Depends(usuario_atual)):
    db.excluir_cartao(cartao_id, usuario_id=usuario["id"])


@router.get("/estudar")
def estudar_tudo(limite: int = Query(default=60, ge=1, le=200), usuario=Depends(usuario_atual)):
    """A fila do dia atravessando todos os baralhos. Sem isto, oito baralhos
    vencidos viram oito sessões."""
    return _fila(None, usuario, limite)


@router.post("/{cartao_id}/desfazer")
def desfazer(cartao_id: int, usuario=Depends(usuario_atual)):
    if not db.desfazer_revisao_cartao(cartao_id, usuario_id=usuario["id"]):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Não há nota para desfazer neste cartão.")
    return {"ok": True}


def _fila(baralho_id, usuario, limite):
    cartoes = db.cartoes_para_estudar(baralho_id, usuario_id=usuario["id"], limite=limite)
    return {
        "cartoes": [
            dict(c, prazos=sr.prazos_do_cartao(c["id"], usuario_id=usuario["id"]))
            for c in cartoes
        ]
    }


@router.get("/baralhos/{baralho_id}/estudar")
def estudar(baralho_id: int, limite: int = Query(default=40, ge=1, le=200), usuario=Depends(usuario_atual)):
    """O lote da sessão de estudo, com os prazos de cada nota já embutidos.

    Mesma decisão do `/praticar/sessao` (MIGRACAO.md §0): o lote inteiro vem de
    uma vez, para não haver ida ao servidor entre um cartão e o próximo. Aqui
    não há gabarito a proteger — o conteúdo é dela.
    """
    if db.obter_baralho(baralho_id, usuario_id=usuario["id"]) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Baralho não encontrado.")
    return _fila(baralho_id, usuario, limite)


@router.post("/{cartao_id}/avaliar")
def avaliar(cartao_id: int, dados: NotaCartaoIn, usuario=Depends(usuario_atual)):
    estado = sr.avaliar_cartao(cartao_id, dados.qualidade, usuario_id=usuario["id"])
    if estado is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cartão não encontrado.")
    return {"proxima_revisao": estado["proxima_revisao"], "intervalo_dias": estado["intervalo_dias"]}
