"""
Rotina diária da plataforma, rodada pelo timer do systemd às 8h de Brasília
(`deploy/residencia-rotina.timer`):

1. **Lembrete de revisão por e-mail** — só para quem ligou no Perfil (é
   opcional e desligado por padrão, decisão do usuário em 26/09), confirmou o
   e-mail e tem revisão vencida hoje, com a mesma conta da aba (casos dentro da
   meta diária e cartões vencidos). Um por dia no máximo.
2. **Relatório do dia anterior** para quem está em ADMIN_EMAILS: quem estudou,
   contas novas, questões suspeitas e erros do app. Um por dia no máximo.

Por padrão só simula: mostra o que mandaria e não envia nem marca nada. Envia
com --enviar. Sem BREVO_API_KEY (esta máquina), `enviar_email` só escreve no log.

    python scripts/rotina_diaria.py            # simula
    python scripts/rotina_diaria.py --enviar   # envia — é o que o timer roda
"""

import argparse
import datetime
import os
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import db  # noqa: E402
import repeticao_espacada as sr  # noqa: E402
from api.email import enviar_email  # noqa: E402
from api.email_modelo import lembrete_revisao, relatorio_diario  # noqa: E402

APP_URL = os.environ.get("APP_URL", "https://qualaconduta.com.br").rstrip("/")
ADMIN_URL = os.environ.get("ADMIN_URL", "https://admin.qualaconduta.com.br").rstrip("/")


def lembretes(hoje, enviar):
    enviados = 0
    for conta in db.contas_para_lembrete(hoje):
        resumo = sr.resumo_revisao_hoje(usuario_id=conta["id"], meta=conta["meta_revisao_diaria"])
        cartoes = db.contar_cartoes_vencidos(usuario_id=conta["id"])
        if resumo["hoje"] == 0 and cartoes == 0:
            continue  # nada vencido: nenhum e-mail
        assunto, texto, html = lembrete_revisao(
            casos=resumo["hoje"], cartoes=cartoes,
            segundos_por_caso=resumo["segundos_por_caso"], app_url=APP_URL,
        )
        if not enviar:
            print(f"  lembrete para a conta {conta['id']}: {assunto}")
            continue
        if enviar_email(conta["email"], assunto, texto, html):
            db.marcar_lembrete_enviado(conta["id"], hoje)
            enviados += 1
    return enviados


def relatorio(hoje, enviar):
    ontem = hoje - datetime.timedelta(days=1)
    assunto, texto, html = relatorio_diario(
        dia=ontem, resumo=db.resumo_do_dia(ontem), suspeitas=db.questoes_suspeitas(),
        erros=db.erros_front_recentes(dias=1), admin_url=ADMIN_URL,
    )
    if not enviar:
        print(f"  relatório: {assunto}")
        return 0
    # A trava vem antes do envio: se o timer rodar duas vezes, o segundo não repete.
    if not db.reservar_envio_diario("relatorio", ontem):
        return 0
    return sum(enviar_email(email, assunto, texto, html) for email in sorted(db.emails_admin()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--enviar", action="store_true")
    args = parser.parse_args()
    hoje = db.hoje_br()
    print(f"Rotina de {hoje:%d/%m/%Y} ({'enviando' if args.enviar else 'simulação, nada é enviado'})")
    print(f"Lembretes enviados: {lembretes(hoje, args.enviar)}")
    print(f"Relatórios enviados: {relatorio(hoje, args.enviar)}")


if __name__ == "__main__":
    main()
