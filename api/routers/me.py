import base64
import binascii
import hashlib

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

import db
from api.deps import eh_admin, usuario_atual
from api.schemas import (
    FotoIn, MeOut, MetaRevisaoIn, NovidadesIn, PerfilIn, ProvaAlvoIn, TemaIn,
)

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
        foto_versao=usuario["foto_versao"],
        cartoes_hoje=db.contar_cartoes_vencidos(usuario_id=usuario["id"]),
    )


@router.patch("/tema")
def atualizar_tema(dados: TemaIn, usuario=Depends(usuario_atual)):
    db.atualizar_tema_usuario(usuario["id"], dados.tema)
    return {"tema": dados.tema}


@router.get("/foto")
def obter_foto(request: Request, usuario=Depends(usuario_atual)):
    """A foto da própria conta. Só a dela: não existe tela que mostre o avatar
    de outra pessoa, então não existe rota para isso.

    Mesmo cache da figura de questão: ETag do conteúdo e `private`, porque a
    resposta depende da sessão e não pertence a nenhum proxy do caminho. Como
    a URL carrega a versão, um ano de cache é seguro — foto nova é URL nova.
    """
    linha = db.obter_foto_perfil(usuario["id"])
    if linha is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sem foto de perfil.")
    imagem = bytes(linha["imagem"])
    etag = '"%s"' % hashlib.sha256(imagem).hexdigest()
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers={"ETag": etag})
    return Response(
        content=imagem,
        media_type=linha["mime"],
        headers={"ETag": etag, "Cache-Control": "private, max-age=31536000, immutable"},
    )


@router.put("/foto")
def enviar_foto(dados: FotoIn, usuario=Depends(usuario_atual)):
    """Recebe a foto já redimensionada pelo navegador.

    Duas conferências que são segurança, não estilo: o **tamanho** dos bytes
    decodificados (o cliente pode mandar o que quiser, não só o que a nossa
    tela manda) e a **assinatura** do arquivo contra o tipo declarado — sem
    isso, um SVG com script dentro entraria como `image/png` e voltaria a ser
    servido da nossa origem.
    """
    if dados.mime not in db.FOTO_MIMES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Use uma imagem JPEG, PNG ou WebP.")
    bruto = dados.dados.split(",", 1)[-1]  # aceita data URL ou base64 puro
    try:
        imagem = base64.b64decode(bruto, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Não foi possível ler essa imagem.")
    if len(imagem) > db.FOTO_MAX_BYTES:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE,
            "Essa imagem é grande demais. Tente uma menor.",
        )
    if not imagem.startswith(db.FOTO_MIMES[dados.mime]):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "O arquivo não é do tipo que diz ser.")
    return {"foto_versao": db.definir_foto_perfil(usuario["id"], imagem, dados.mime)}


@router.delete("/foto", status_code=status.HTTP_204_NO_CONTENT)
def apagar_foto(usuario=Depends(usuario_atual)):
    db.remover_foto_perfil(usuario["id"])


@router.patch("/perfil")
def atualizar_perfil(dados: PerfilIn, usuario=Depends(usuario_atual)):
    nome, cor = db.atualizar_perfil(usuario["id"], dados.nome, dados.cor)
    return {"nome": nome, "cor_perfil": cor}


@router.get("/marcadas")
def listar_marcadas(usuario=Depends(usuario_atual)):
    """As questões que ela marcou, em resumo: enunciado e classificação, sem
    gabarito nem explicação. Para revê-las de verdade existe o filtro
    `apenas_marcadas` do Praticar, que passa pelo teto diário como o resto."""
    return {"questoes": [dict(q) for q in db.resumo_questoes_marcadas(usuario_id=usuario["id"])]}


@router.patch("/prova")
def definir_prova(dados: ProvaAlvoIn, usuario=Depends(usuario_atual)):
    """A data que alimenta a contagem regressiva da barra e do Painel. Existia
    no banco desde sempre e não tinha como ser definida pelo app."""
    db.definir_prova_alvo(usuario["id"], dados.data)
    return {"prova_alvo": dados.data}


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
