from fastapi import APIRouter, Depends, Response, status

import db
from api.deps import eh_admin, usuario_atual
from api.schemas import MeOut, MetaRevisaoIn, NovidadesIn, PerfilIn, TemaIn

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=MeOut)
def obter_me(usuario=Depends(usuario_atual)):
    ofensiva_dias, respondeu_hoje = db.calcular_ofensiva(usuario_id=usuario["id"])
    return MeOut(
        id=usuario["id"],
        email=usuario["email"],
        is_admin=eh_admin(usuario),
        email_confirmado=usuario["email_confirmado_em"] is not None,
        tema=usuario["tema"],
        prova_alvo=usuario["data_prova_alvo"],
        ofensiva_dias=ofensiva_dias,
        respondeu_hoje=respondeu_hoje,
        respondidas_hoje=db.contar_respondidas_hoje(usuario_id=usuario["id"]),
        total_questoes=db.contar_questoes(),
        meta_revisao_diaria=usuario["meta_revisao_diaria"],
        novidades_vistas=usuario["novidades_vistas"],
        nome=usuario["nome"],
        cor_perfil=usuario["cor_perfil"] or db.COR_PERFIL_PADRAO,
    )


@router.patch("/tema")
def atualizar_tema(dados: TemaIn, usuario=Depends(usuario_atual)):
    db.atualizar_tema_usuario(usuario["id"], dados.tema)
    return {"tema": dados.tema}


@router.patch("/perfil")
def atualizar_perfil(dados: PerfilIn, usuario=Depends(usuario_atual)):
    nome, cor = db.atualizar_perfil(usuario["id"], dados.nome, dados.cor)
    return {"nome": nome, "cor_perfil": cor}


@router.patch("/novidades")
def marcar_novidades(dados: NovidadesIn, usuario=Depends(usuario_atual)):
    """Guarda até onde esta conta já leu as novidades. O id vem do front, que
    é onde a lista mora — o servidor não precisa conhecer as entradas para
    lembrar qual foi a última vista."""
    db.marcar_novidades_vistas(usuario["id"], dados.visto)
    return {"novidades_vistas": dados.visto}


@router.patch("/meta-revisao")
def atualizar_meta_revisao(dados: MetaRevisaoIn, usuario=Depends(usuario_atual)):
    db.atualizar_meta_revisao(usuario["id"], dados.meta)
    return {"meta_revisao_diaria": dados.meta}


@router.get("/relatos-resolvidos")
def relatos_resolvidos(usuario=Depends(usuario_atual)):
    """Questões que este aluno reportou e que já foram corrigidas, ainda não
    mostradas a ele."""
    return [dict(r) for r in db.relatos_resolvidos_a_avisar(usuario["id"])]


@router.post("/relatos-resolvidos/vistos", status_code=status.HTTP_204_NO_CONTENT)
def marcar_relatos_vistos(usuario=Depends(usuario_atual)):
    db.marcar_relatos_avisados(usuario["id"])
    return Response(status_code=status.HTTP_204_NO_CONTENT)
