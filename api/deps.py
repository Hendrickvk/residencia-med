import os

from fastapi import Depends, HTTPException, Request, status

import db
from api.security import COOKIE_NOME, decodificar_token

ADMIN_EMAILS = {
    e.strip().lower()
    for e in os.environ.get("ADMIN_EMAILS", "hendrickvk@gmail.com").split(",")
    if e.strip()
}


def usuario_atual(request: Request):
    token = request.cookies.get(COOKIE_NOME)
    usuario_id = decodificar_token(token) if token else None
    if usuario_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sessão inválida ou expirada.")
    usuario = db.obter_usuario(usuario_id)
    if usuario is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sessão inválida ou expirada.")
    return usuario


def exigir_admin(usuario=Depends(usuario_atual)):
    if usuario["email"] not in ADMIN_EMAILS:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Ação restrita a administradores.")
    return usuario


def eh_admin(usuario) -> bool:
    return usuario["email"] in ADMIN_EMAILS
