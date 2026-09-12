"""
Popula um usuário de demonstração com histórico realista, conforme
MIGRACAO.md §7: "um usuário de demonstração populado com algo como 400
respostas espalhadas por 8 semanas, com desempenho desigual entre áreas."

Usa questões REAIS já cadastradas (não fabrica conteúdo) — só o histórico
de respostas (quem respondeu o quê, quando, e se acertou) é sintético.

Rodar uma vez, em produção, antes do primeiro link ser compartilhado:
    python scripts/seed_demo_user.py

Idempotente por checagem simples: se a conta demo já tiver qualquer
resposta registrada, o script não faz nada (evita duplicar histórico se
rodado de novo por engano).
"""

import datetime
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bcrypt  # noqa: E402

import db  # noqa: E402

EMAIL_DEMO = "demo@residenciamed.com"
SENHA_DEMO = "ResidenciaDemo2026!"
TOTAL_RESPOSTAS = 400
DIAS_JANELA = 56  # 8 semanas
HORARIOS_PLAUSIVEIS = [7, 8, 9, 19, 20, 21, 22]


def _hash(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def obter_ou_criar_demo() -> int:
    usuario = db.obter_usuario_por_email(EMAIL_DEMO)
    if usuario:
        return usuario["id"]
    usuario_id = db.criar_usuario(EMAIL_DEMO, _hash(SENHA_DEMO))
    if usuario_id is None:
        # corrida rara com outra execução — a conta já existe, só buscar de novo
        return db.obter_usuario_por_email(EMAIL_DEMO)["id"]
    return usuario_id


def main():
    usuario_id = obter_ou_criar_demo()

    with db.get_conn() as conn:
        ja_tem = conn.execute(
            "SELECT COUNT(*) AS n FROM respostas WHERE usuario_id = ?", (usuario_id,)
        ).fetchone()["n"]
    if ja_tem > 0:
        print(f"Conta demo já tem {ja_tem} resposta(s) — nada a fazer (rode só uma vez).")
        return

    areas = db.listar_areas()
    questoes_por_area = {}
    with db.get_conn() as conn:
        for area in areas:
            linhas = conn.execute(
                "SELECT id, resposta_correta, alternativas FROM questoes WHERE area_id = ?", (area["id"],)
            ).fetchall()
            if linhas:
                questoes_por_area[area["id"]] = linhas

    areas_com_questoes = [a for a in areas if a["id"] in questoes_por_area]
    if not areas_com_questoes:
        print("Nenhuma área tem questão cadastrada ainda — rode isso depois de importar o banco de questões.")
        return

    # Desempenho desigual "de propósito": sorteia uma faixa de taxa de
    # acerto por área, ampla o bastante pra o Painel apontar uma lacuna de
    # verdade em vez de tudo parecido.
    taxa_por_area = {
        area["id"]: random.choice(
            [random.uniform(0.75, 0.92), random.uniform(0.50, 0.68), random.uniform(0.25, 0.42)]
        )
        for area in areas_com_questoes
    }

    agora = datetime.datetime.now()
    inseridas = 0

    with db.get_conn() as conn:
        for _ in range(TOTAL_RESPOSTAS):
            area = random.choice(areas_com_questoes)
            questao = random.choice(questoes_por_area[area["id"]])
            alternativas = questao["alternativas"]
            if isinstance(alternativas, str):
                alternativas = json.loads(alternativas)
            letras = list(alternativas.keys())

            acertou = random.random() < taxa_por_area[area["id"]]
            if acertou:
                escolha = questao["resposta_correta"]
            else:
                erradas = [l for l in letras if l != questao["resposta_correta"]] or letras
                escolha = random.choice(erradas)

            # Viés leve pros dias mais recentes — mais parecido com uso
            # real (intensidade decrescente quanto mais no passado).
            peso = random.random() ** 1.5
            quando = agora - datetime.timedelta(seconds=peso * DIAS_JANELA * 86400)
            quando = quando.replace(hour=random.choice(HORARIOS_PLAUSIVEIS), minute=random.randint(0, 59))

            confianca = None
            if acertou:
                confianca = "seguro" if random.random() < 0.7 else "chute"

            conn.execute(
                """
                INSERT INTO respostas (usuario_id, questao_id, resposta_dada, correta, respondida_em, confianca)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (usuario_id, questao["id"], escolha, int(acertou), quando.isoformat(), confianca),
            )
            inseridas += 1

    print(f"{inseridas} respostas semeadas para {EMAIL_DEMO} (senha: {SENHA_DEMO}).")
    print("Desempenho por área sorteado (menor = pior, aparece como lacuna no Painel):")
    for area in areas_com_questoes:
        print(f"  {area['nome']}: ~{taxa_por_area[area['id']] * 100:.0f}%")


if __name__ == "__main__":
    main()
