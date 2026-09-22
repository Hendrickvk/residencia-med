from fastapi import HTTPException, Request, status

import db
from api.security import COOKIE_NOME, decodificar_token

# Lido a cada chamada, e não uma vez no import, para o `ADMIN_EMAILS` do
# ambiente valer sem reiniciar o processo — e porque guardar a lista num módulo
# global era o que fazia o e-mail do admin virar constante no código.


def usuario_atual(request: Request):
    token = request.cookies.get(COOKIE_NOME)
    usuario_id = decodificar_token(token) if token else None
    if usuario_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sessão inválida ou expirada.")
    usuario = db.obter_usuario(usuario_id)
    if usuario is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sessão inválida ou expirada.")
    return usuario


def eh_admin(usuario) -> bool:
    return usuario["email"] in db.emails_admin()
