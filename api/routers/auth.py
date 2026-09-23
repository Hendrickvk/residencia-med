import datetime
import hashlib
import os
import secrets
import time

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

import db
from api.deps import usuario_atual
from api.email import enviar_email
from api.email_modelo import montar_html
from api.schemas import ConfirmarEmailIn, CredenciaisIn, EsqueciSenhaIn, RedefinirSenhaIn
from api.security import (
    COOKIE_NOME, COOKIE_SECURE, JWT_EXPIRA_HORAS, criar_token, decodificar_token,
    hash_senha, verificar_senha,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# Endereço do front, para montar o link do e-mail. Em produção vira o domínio
# do DuckDNS junto com o resto das env vars do deploy.
APP_URL = os.environ.get("APP_URL", "http://localhost:5173").rstrip("/")
# Pedidos de redefinição por conta em 15 minutos (db.contar_tokens_recentes).
LIMITE_PEDIDOS = 3

# Força bruta no login: o "esqueci minha senha" já tinha limite e o login não,
# então tentar milhares de senhas contra uma conta conhecida era grátis — e o
# e-mail do admin estava escrito no código, num repositório público.
JANELA_LOGIN_S = 300
MAX_TENTATIVAS_LOGIN = 10

# Cadastro em massa: a porta continua **aberta a qualquer pessoa** (decisão do
# usuário em 2026-09-23 — não restringir quem cria conta), mas não a um script.
# O teto diário de prática é por conta, então conta grátis e ilimitada o
# contornava: 3 cadastros levavam o banco inteiro. Cinco contas por IP por hora
# é muito acima de qualquer uso real (uma pessoa cria conta uma vez) e abaixo
# do que compensa para quem raspa. Não resolve quem tem muitos IPs — isso é
# confirmação de e-mail, que é outro trabalho e está registrado como tal.
JANELA_SIGNUP_S = 3600
MAX_SIGNUPS_IP = 5

# ponytail: contador na memória do processo — zera no restart e não é
# compartilhado entre workers. A API roda em um; com vários, isto vira tabela.
_TENTATIVAS_LOGIN: dict[str, list[float]] = {}
_JANELA_MAX_S = max(JANELA_LOGIN_S, JANELA_SIGNUP_S)


def _chave_tentativa(request: Request, email: str) -> str:
    return "%s|%s" % (request.client.host if request.client else "?", email.strip().lower())


def _chave_ip(request: Request) -> str:
    """Cadastro conta por IP, e não por IP+e-mail como o login: cada tentativa
    de cadastro usa um e-mail diferente, então a chave do login não limitaria
    nada aqui."""
    return "signup|%s" % (request.client.host if request.client else "?")


def _bloqueado(chave: str, maximo: int, janela_s: float) -> bool:
    agora = time.monotonic()
    recentes = [t for t in _TENTATIVAS_LOGIN.get(chave, []) if agora - t < janela_s]
    _TENTATIVAS_LOGIN[chave] = recentes
    return len(recentes) >= maximo


def _registrar_tentativa(chave: str) -> None:
    _TENTATIVAS_LOGIN.setdefault(chave, []).append(time.monotonic())
    # O dicionário nunca encolheria sozinho: sem isso, cada par IP+e-mail
    # tentado deixaria uma entrada para sempre no processo.
    if len(_TENTATIVAS_LOGIN) > 5000:
        agora = time.monotonic()
        for k in [k for k, v in _TENTATIVAS_LOGIN.items() if all(agora - t > _JANELA_MAX_S for t in v)]:
            del _TENTATIVAS_LOGIN[k]


def _hash_token(token: str) -> str:
    """O banco guarda só isto: token vazado do banco não redefine nada."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _enviar_confirmacao(usuario) -> None:
    """Cria um token e manda o e-mail de confirmação. Nunca levanta: o cadastro
    não pode falhar porque o Brevo estava fora do ar — a conta existe, o
    reenvio está na tela, e sem `BREVO_API_KEY` o link sai no log do servidor,
    que é o caminho de desenvolvimento."""
    token = secrets.token_urlsafe(32)
    db.criar_token_confirmacao(usuario["id"], _hash_token(token))
    url = f"{APP_URL}/confirmar/{token}"
    enviar_email(
        usuario["email"],
        "Confirme o seu e-mail na Conduta",
        "Alguém (esperamos que você) criou uma conta na Conduta com este "
        "endereço. Confirme para liberar as questões:\n\n"
        f"{url}\n\n"
        f"O link vale {db.CONFIRMACAO_VALIDA_HORAS} horas e serve uma vez só. "
        "Se não foi você quem criou a conta, pode ignorar este e-mail.\n",
        html=montar_html(
            titulo="Confirme o seu e-mail",
            # Duas linhas e o botão. O e-mail não explica por que a
            # confirmação existe: quem recebeu quer entrar, não entender a
            # política de cadastro. O aparte entre parênteses é o mesmo do
            # e-mail de senha, aprovado pelo usuário em 2026-09-23 — é leve
            # porque é honesto: a plataforma de fato não sabe se foi ela.
            paragrafos=[
                "Alguém (esperamos que você) criou uma conta na Conduta com "
                "este endereço.",
                "Confirme para liberar as questões.",
            ],
            botao_texto="Confirmar meu e-mail",
            botao_url=url,
            rodape=(
                f"O link vale {db.CONFIRMACAO_VALIDA_HORAS} horas e serve uma vez só. "
                "Se não foi você quem criou a conta, pode ignorar esta mensagem."
            ),
        ),
    )


def _definir_cookie_sessao(response: Response, usuario_id: int, token_version: int):
    response.set_cookie(
        COOKIE_NOME, criar_token(usuario_id, token_version),
        httponly=True, samesite="lax", secure=COOKIE_SECURE,
        max_age=JWT_EXPIRA_HORAS * 3600,
    )


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(dados: CredenciaisIn, request: Request, response: Response):
    chave = _chave_ip(request)
    if _bloqueado(chave, MAX_SIGNUPS_IP, JANELA_SIGNUP_S):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Muitas contas criadas deste endereço. Tente de novo mais tarde.",
        )
    # Conta a tentativa antes de saber se deu certo: senão o 409 do e-mail
    # repetido sairia de graça e o limite não limitaria nada.
    _registrar_tentativa(chave)
    usuario_id = db.criar_usuario(dados.email, hash_senha(dados.senha))
    if usuario_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe uma conta com esse e-mail.")
    usuario = db.obter_usuario(usuario_id)
    _enviar_confirmacao(usuario)
    # Entra mesmo sem confirmar: ela vê o Painel, o aviso e o botão de
    # reenviar. Trancar na porta de entrada faria quem não recebeu o e-mail
    # não ter nem onde pedir de novo. O que a confirmação libera é o conteúdo.
    # A versão vem do banco em vez de um 0 literal: conta nova começa em 0
    # hoje, e um default que mude depois não pode sair daqui desalinhado.
    _definir_cookie_sessao(response, usuario_id, usuario["token_version"])
    return {"id": usuario_id, "email": dados.email.strip().lower()}


@router.post("/login")
def login(dados: CredenciaisIn, request: Request, response: Response):
    chave = _chave_tentativa(request, dados.email)
    if _bloqueado(chave, MAX_TENTATIVAS_LOGIN, JANELA_LOGIN_S):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Muitas tentativas. Espere alguns minutos antes de tentar de novo.",
        )
    usuario = db.obter_usuario_por_email(dados.email)
    if usuario is None or not verificar_senha(dados.senha, usuario["senha_hash"]):
        _registrar_tentativa(chave)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou senha incorretos.")
    # Acertou: a conta não fica penalizada pelos erros de digitação de antes.
    _TENTATIVAS_LOGIN.pop(chave, None)
    _definir_cookie_sessao(response, usuario["id"], usuario["token_version"])
    return {"id": usuario["id"], "email": usuario["email"]}


@router.post("/logout")
def logout(request: Request, response: Response):
    """Apagar o cookie é o que o navegador dela vê; incrementar a versão é o
    que vale contra um token já copiado, que continuaria valendo pelas 12 h
    restantes. Sem sessão não há o que revogar, e a resposta é a mesma: quem
    não está logado não precisa saber se havia sessão."""
    dados = decodificar_token(request.cookies.get(COOKIE_NOME) or "")
    if dados is not None:
        db.invalidar_sessoes(dados[0])
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
        url = f"{APP_URL}/senha/{token}"
        enviar_email(
            usuario["email"],
            "Redefinir a sua senha na Conduta",
            "Alguém (esperamos que você) pediu para redefinir a senha desta conta.\n\n"
            f"Escolha uma senha nova aqui, nos próximos {minutos} minutos:\n"
            f"{APP_URL}/senha/{token}\n\n"
            "O link vale uma vez só. Se não foi você, ignore este e-mail: "
            "sua senha continua a mesma.\n",
            html=montar_html(
                titulo="Redefinir a sua senha",
                paragrafos=[
                    "Alguém (esperamos que você) pediu para redefinir a senha "
                    "desta conta.",
                    f"O botão abaixo vale pelos próximos {minutos} minutos e "
                    "serve uma vez só.",
                ],
                botao_texto="Escolher uma senha nova",
                botao_url=url,
                rodape=(
                    "Se não foi você, pode ignorar esta mensagem: sua senha "
                    "continua a mesma, e ninguém entra sem abrir este link."
                ),
            ),
        )
    return {"ok": True}


@router.post("/confirmar")
def confirmar_email(dados: ConfirmarEmailIn):
    """Segundo passo do cadastro, chegando pelo link do e-mail.

    Rota pública e sem sessão: o link costuma ser aberto no celular, que não é
    o navegador onde ela criou a conta. Confirmar **não** dá sessão — seria um
    link mágico, poder que este e-mail não precisa ter.

    Token inexistente, expirado e já usado devolvem a mesma mensagem, como no
    fluxo de senha: detalhar só ajudaria quem está testando tokens no escuro.
    """
    registro = db.obter_token_confirmacao(_hash_token(dados.token))
    if registro is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Este link não vale mais. Entre na sua conta e peça outro.",
        )
    db.confirmar_email(registro["usuario_id"], registro["id"])
    return {"ok": True}


@router.post("/confirmar/reenviar")
def reenviar_confirmacao(usuario=Depends(usuario_atual)):
    """Pede outro link. Exige sessão, então não é oráculo de quem tem conta —
    ao contrário do `/senha/esqueci`, aqui já se sabe quem está pedindo.

    Conta confirmada responde `ok` sem mandar nada: não é erro, e o aviso na
    tela pode estar velho (ela confirmou em outra aba).
    """
    if usuario["email_confirmado_em"] is not None:
        return {"ok": True}
    if db.contar_confirmacoes_recentes(usuario["id"]) >= LIMITE_PEDIDOS:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Já pedimos alguns links agora há pouco. Confira a caixa de spam e "
            "espere alguns minutos.",
        )
    _enviar_confirmacao(usuario)
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
    _definir_cookie_sessao(response, usuario["id"], usuario["token_version"])
    return {"id": usuario["id"], "email": usuario["email"]}
