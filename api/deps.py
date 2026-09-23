from fastapi import Depends, HTTPException, Request, status

import db
from api.security import COOKIE_NOME, decodificar_token

# Lido a cada chamada, e não uma vez no import, para o `ADMIN_EMAILS` do
# ambiente valer sem reiniciar o processo — e porque guardar a lista num módulo
# global era o que fazia o e-mail do admin virar constante no código.


def usuario_atual(request: Request):
    token = request.cookies.get(COOKIE_NOME)
    dados = decodificar_token(token) if token else None
    if dados is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sessão inválida ou expirada.")
    usuario_id, versao = dados
    usuario = db.obter_usuario(usuario_id)
    if usuario is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sessão inválida ou expirada.")
    # Revogação de sessão (HISTORICO.md, item 4): o logout e a redefinição de
    # senha incrementam `token_version`, e é esta comparação que faz o token
    # antigo parar de valer antes das 12 h dele. Não custa consulta nenhuma —
    # o usuário já era lido aqui.
    if usuario["token_version"] != versao:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sessão encerrada. Entre de novo.")
    return usuario


def usuario_confirmado(usuario=Depends(usuario_atual)):
    """Sessão **e** e-mail confirmado. Fica nos endpoints que entregam
    conteúdo (a sessão de prática e a criação de simulado), não na sessão
    inteira: quem acabou de se cadastrar precisa poder entrar, ver o aviso e
    pedir outro link. 403 e não 401 de propósito — 401 mandaria a tela para o
    login, e ela está logada; o que falta é outra coisa."""
    if usuario["email_confirmado_em"] is None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Confirme o seu e-mail para liberar as questões. "
            "O link está na sua caixa de entrada — dá para pedir outro no Painel.",
        )
    return usuario


def eh_admin(usuario) -> bool:
    return usuario["email"] in db.emails_admin()
