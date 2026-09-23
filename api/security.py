"""
Autenticação da API: hash de senha (bcrypt) e token de sessão (JWT em
cookie httpOnly), conforme decidido no MIGRACAO.md §3.

Não reimporta `auth.py` (a versão Streamlit) porque esse módulo importa
`streamlit` e `ui.py` no topo do arquivo — dependência desnecessária para
um processo de API que não deveria carregar a camada de view descartada.
Duplicar duas funções de bcrypt é mais barato que acoplar as duas camadas.
"""

import datetime
import logging
import os
import secrets

import bcrypt
import jwt

def _segredo_jwt() -> str:
    """Segredo de assinatura da sessão, do ambiente — sem default no código.

    Tinha um default fixo aqui, e este repositório é público: qualquer pessoa
    podia assinar um cookie válido para qualquer usuário (inclusive o admin) se
    a variável faltasse em produção — um EnvironmentFile esquecido no systemd
    bastava, e a API subia normalmente, sem um aviso. O aleatório falha para o
    lado seguro: em desenvolvimento funciona sem configurar nada, ao preço de a
    sessão não sobreviver a um restart (por isso o `.env` local tem uma chave
    fixa), e em produção o aviso aparece no log.
    """
    do_ambiente = os.environ.get("JWT_SECRET_KEY")
    if do_ambiente:
        return do_ambiente
    logging.getLogger("conduta.security").warning(
        "JWT_SECRET_KEY não definida: usando segredo aleatório deste processo. "
        "As sessões caem a cada reinício. Em produção, defina a variável."
    )
    return secrets.token_urlsafe(32)


JWT_SECRET = _segredo_jwt()
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


def criar_token(usuario_id: int, token_version: int) -> str:
    """`tv` é a versão de sessão da conta (`usuarios.token_version`), conferida
    a cada requisição em `deps.usuario_atual`. É o que torna o logout uma
    revogação de verdade: o JWT é stateless e vale 12 h, então sem isso apagar
    o cookie não faz nada contra um token já copiado."""
    expira_em = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=JWT_EXPIRA_HORAS)
    return jwt.encode(
        {"sub": str(usuario_id), "tv": int(token_version), "exp": expira_em},
        JWT_SECRET, algorithm=JWT_ALGORITHM,
    )


def decodificar_token(token: str) -> tuple[int, int] | None:
    """Devolve (usuario_id, token_version) ou None. Token sem `tv` é token de
    antes desta mudança: cai como inválido, de propósito — o lado seguro é
    todo mundo refazer o login uma vez, não uma sessão antiga passar sem
    conferência."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return int(payload["sub"]), int(payload["tv"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        return None
