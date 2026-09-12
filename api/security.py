"""
Autenticação da API: hash de senha (bcrypt) e token de sessão (JWT em
cookie httpOnly), conforme decidido no MIGRACAO.md §3.

Não reimporta `auth.py` (a versão Streamlit) porque esse módulo importa
`streamlit` e `ui.py` no topo do arquivo — dependência desnecessária para
um processo de API que não deveria carregar a camada de view descartada.
Duplicar duas funções de bcrypt é mais barato que acoplar as duas camadas.
"""

import datetime
import os

import bcrypt
import jwt

JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "dev-insecure-secret-troque-em-producao")
JWT_ALGORITHM = "HS256"
JWT_EXPIRA_HORAS = 12
COOKIE_NOME = "residencia_med_session"
# Desligado em dev/testes (TestClient e `uvicorn --reload` local servem em
# http://, e um cookie Secure nunca é reenviado por um cliente HTTP correto
# fora de https://) — ligar via env var atrás do domínio real (MIGRACAO.md §7).
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, hash_armazenado: str) -> bool:
    return bcrypt.checkpw(senha.encode("utf-8"), hash_armazenado.encode("utf-8"))


def criar_token(usuario_id: int) -> str:
    expira_em = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=JWT_EXPIRA_HORAS)
    return jwt.encode({"sub": str(usuario_id), "exp": expira_em}, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decodificar_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return int(payload["sub"])
    except jwt.PyJWTError:
        return None
