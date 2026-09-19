import datetime
import hashlib
import os
import secrets

from fastapi import APIRouter, HTTPException, Response, status

import db
from api.email import enviar_email
from api.schemas import CredenciaisIn, EsqueciSenhaIn, RedefinirSenhaIn
from api.security import COOKIE_NOME, COOKIE_SECURE, JWT_EXPIRA_HORAS, criar_token, hash_senha, verificar_senha

router = APIRouter(prefix="/auth", tags=["auth"])

# Endereço do front, para montar o link do e-mail. Em produção vira o domínio
# do DuckDNS junto com o resto das env vars do deploy.
APP_URL = os.environ.get("APP_URL", "http://localhost:5173").rstrip("/")
# Pedidos de redefinição por conta em 15 minutos (db.contar_tokens_recentes).
LIMITE_PEDIDOS = 3


def _hash_token(token: str) -> str:
    """O banco guarda só isto: token vazado do banco não redefine nada."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


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


@router.post("/senha/esqueci")
def esqueci_senha(dados: EsqueciSenhaIn):
    """Primeiro passo do "esqueci minha senha".

    Responde **sempre** a mesma coisa, exista ou não a conta: a diferença
    viraria um oráculo para descobrir quem tem cadastro na plataforma. Por
    isso nada aqui é `raise` — nem quando o envio falha, nem quando a conta é
    inexistente, nem quando o limite de pedidos foi atingido.
    """
    usuario = db.obter_usuario_por_email(dados.email)
    if usuario is not None and db.contar_tokens_recentes(usuario["id"]) < LIMITE_PEDIDOS:
        token = secrets.token_urlsafe(32)
        expira_em = db.criar_token_senha(usuario["id"], _hash_token(token))
        minutos = round((expira_em - datetime.datetime.now()).total_seconds() / 60)
        enviar_email(
            usuario["email"],
            "Redefinir a sua senha na Conduta",
            "Alguém (esperamos que você) pediu para redefinir a senha desta conta.\n\n"
            f"Escolha uma senha nova aqui, nos próximos {minutos} minutos:\n"
            f"{APP_URL}/senha/{token}\n\n"
            "O link vale uma vez só. Se não foi você, ignore este e-mail: "
            "sua senha continua a mesma.\n",
        )
    return {"ok": True}


@router.post("/senha/redefinir")
def redefinir_senha(dados: RedefinirSenhaIn, response: Response):
    """Segundo passo: troca a senha e já entra com a conta.

    Token inválido, expirado ou usado devolvem a mesma mensagem — a tela não
    tem o que fazer de diferente em cada caso, e detalhar ajudaria só quem
    está testando tokens no escuro.
    """
    registro = db.obter_token_senha(_hash_token(dados.token))
    if registro is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Este link não vale mais. Peça outro.")
    db.redefinir_senha(registro["usuario_id"], hash_senha(dados.senha), registro["id"])
    usuario = db.obter_usuario(registro["usuario_id"])
    _definir_cookie_sessao(response, usuario["id"])
    return {"id": usuario["id"], "email": usuario["email"]}
