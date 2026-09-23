"""
Envio de e-mail transacional: redefinição de senha e confirmação de conta.

O corpo vai em texto e, quando quem chama monta (`email_modelo.py`), também em
HTML com a cara da plataforma.

Usa a API HTTP do Brevo em vez de SMTP por dois motivos: `httpx` já está no
`requirements.txt` (SMTP exigiria abrir porta e lidar com TLS na mão) e o
Brevo permite remetente verificado por **e-mail**, sem domínio próprio — que é
a situação do projeto enquanto o DuckDNS não sai.

Sem `BREVO_API_KEY` no ambiente, `enviar_email` não finge que enviou: devolve
False e escreve o conteúdo no log do servidor. Em desenvolvimento é isso que
permite copiar o link do terminal; em produção, é o que faz o problema
aparecer no log em vez de virar um e-mail que nunca chega.
"""

import logging
import os

import httpx

logger = logging.getLogger("conduta.email")

BREVO_URL = "https://api.brevo.com/v3/smtp/email"
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
REMETENTE = os.environ.get("EMAIL_REMETENTE", "")
REMETENTE_NOME = os.environ.get("EMAIL_REMETENTE_NOME", "Conduta")
TIMEOUT_S = 10


# Domínios reservados pela RFC 2606/6761: não existem no DNS, então tentar
# entregar neles só gera bounce — e bounce em conta gratuita queima a
# reputação do remetente. As contas de teste da suíte usam `@teste.local`.
DOMINIOS_DE_TESTE = (".local", ".test", ".invalid", ".example", ".localhost")


def envio_configurado() -> bool:
    return bool(BREVO_API_KEY and REMETENTE)


def destinatario_real(email: str) -> bool:
    return not email.strip().lower().endswith(DOMINIOS_DE_TESTE)


def enviar_email(para: str, assunto: str, texto: str, html: str | None = None) -> bool:
    """Devolve True só quando o provedor aceitou a mensagem.

    Nunca levanta: quem chama está sempre num fluxo em que falhar em enviar
    não pode virar erro para o usuário (a resposta do "esqueci minha senha" é
    a mesma exista ou não a conta, e vazar "falha ao enviar" contaria que a
    conta existe).
    """
    if not destinatario_real(para):
        logger.info("Destinatário de domínio reservado (%s): envio ignorado.", para)
        return False
    if not envio_configurado():
        # Só a versão em texto vai para o log: é dela que se copia o link no
        # terminal em desenvolvimento, e o HTML só encheria a tela.
        logger.warning(
            "Envio de e-mail não configurado (BREVO_API_KEY/EMAIL_REMETENTE). "
            "Mensagem que seria enviada para %s:\n%s\n%s", para, assunto, texto,
        )
        return False
    try:
        resposta = httpx.post(
            BREVO_URL,
            headers={"api-key": BREVO_API_KEY, "accept": "application/json"},
            json={
                "sender": {"email": REMETENTE, "name": REMETENTE_NOME},
                "to": [{"email": para}],
                "subject": assunto,
                # Os dois juntos: o cliente escolhe. Sem a versão em texto, o
                # filtro de spam desconfia de mensagem só-HTML, e quem lê em
                # terminal ou leitor de tela fica sem nada.
                "textContent": texto,
                **({"htmlContent": html} if html else {}),
            },
            timeout=TIMEOUT_S,
        )
        if resposta.status_code >= 400:
            logger.error("Brevo recusou o envio para %s: %s %s", para, resposta.status_code, resposta.text[:300])
            return False
        return True
    except httpx.HTTPError as erro:
        logger.error("Falha de rede ao enviar e-mail para %s: %s", para, erro)
        return False
