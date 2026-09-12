from fastapi import APIRouter, HTTPException, Response, status

import db
from api.schemas import CredenciaisIn
from api.security import COOKIE_NOME, COOKIE_SECURE, JWT_EXPIRA_HORAS, criar_token, hash_senha, verificar_senha

router = APIRouter(prefix="/auth", tags=["auth"])


def _definir_cookie_sessao(response: Response, usuario_id: int):
    response.set_cookie(
        COOKIE_NOME, criar_token(usuario_id),
        httponly=True, samesite="lax", secure=COOKIE_SECURE,
        max_age=JWT_EXPIRA_HORAS * 3600,
    )


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(dados: CredenciaisIn, response: Response):
    usuario_id = db.criar_usuario(dados.email, hash_senha(dados.senha))
    if usuario_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe uma conta com esse e-mail.")
    _definir_cookie_sessao(response, usuario_id)
    return {"id": usuario_id, "email": dados.email.strip().lower()}


@router.post("/login")
def login(dados: CredenciaisIn, response: Response):
    usuario = db.obter_usuario_por_email(dados.email)
    if usuario is None or not verificar_senha(dados.senha, usuario["senha_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou senha incorretos.")
    _definir_cookie_sessao(response, usuario["id"])
    return {"id": usuario["id"], "email": usuario["email"]}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NOME)
    return {"ok": True}
