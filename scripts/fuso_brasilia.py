"""
Passa para o horário de Brasília o que o servidor gravou em UTC (HISTORICO.md,
2026-09-25). O servidor e o banco rodam em UTC, e até 25/09 a API gravava a hora
de `datetime.now()` no servidor, que é UTC. Desde então o relógio da plataforma é
`db.agora_br()`, o de Brasília; sem este deslocamento o que já estava gravado
seria lido 3h adiantado: estudo das 21h às 24h no dia seguinte, revisões vencendo
3h depois, tokens valendo 3h a mais.

Desloca −3h, uma vez, as colunas de hora das tabelas que a API grava. Fica de fora
o que é gravado desta máquina, que já roda em Brasília (questões importadas,
relatos resolvidos no admin local), e o que não depende de hora (`cota_pratica`,
que é por dia e zera sozinha). A conta demo, semeada daqui, entra junto: 3h numa
história inventada não mudam nada, e separar complicaria o script.

Por padrão simula numa transação que é desfeita no fim. Grava com --aplicar,
depois de salvar em backups/ os valores anteriores. Uma marca em
`migracoes_dados` impede aplicar duas vezes; --reverter devolve as 3h e apaga a
marca. Antes do --aplicar: `python scripts/backup_banco.py`, e a API parada, para
nada ser gravado em UTC no meio.

    python scripts/fuso_brasilia.py              # simula
    python scripts/fuso_brasilia.py --aplicar    # grava
    python scripts/fuso_brasilia.py --reverter   # desfaz
"""

import argparse
import datetime
import json
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import db  # noqa: E402

MARCA = "fuso_brasilia"

# tabela: (chave, colunas TIMESTAMP, colunas TEXT com a hora em ISO)
COLUNAS = {
    "respostas": (["id"], [], ["respondida_em"]),
    "revisao": (["usuario_id", "questao_id"], ["proxima_revisao"], []),
    "revisao_eventos": (["id"], ["registrado_em", "proxima_revisao"], []),
    "revisao_cartao": (["usuario_id", "cartao_id"], ["proxima_revisao"], []),
    "revisao_cartao_eventos": (["id"], ["registrado_em", "proxima_revisao"], []),
    "simulados": (["id"], [], ["iniciado_em", "finalizado_em"]),
    "questoes_marcadas": (["usuario_id", "questao_id"], [], ["criada_em"]),
    "senha_tokens": (["id"], ["criado_em", "expira_em", "usado_em"], []),
    "confirmacao_tokens": (["id"], ["criado_em", "expira_em", "usado_em"], []),
    "pastas_cartoes": (["id"], ["criada_em"], []),
    "baralhos": (["id"], ["criado_em"], []),
    "cartoes": (["id"], ["criado_em"], []),
}


class Simulacao(Exception):
    """Levantada no fim da simulação para o `get_conn` desfazer a transação."""


def _json(valor):
    return valor.isoformat() if isinstance(valor, (datetime.datetime, datetime.date)) else valor


def main():
    parser = argparse.ArgumentParser()
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument("--aplicar", action="store_true")
    grupo.add_argument("--reverter", action="store_true")
    args = parser.parse_args()
    sinal = "+" if args.reverter else "-"

    try:
        with db.get_conn() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS migracoes_dados (nome TEXT PRIMARY KEY, aplicada_em TIMESTAMP NOT NULL)"
            )
            aplicada = conn.execute("SELECT aplicada_em FROM migracoes_dados WHERE nome = ?", (MARCA,)).fetchone()
            if args.reverter and not aplicada:
                sys.exit("Nada a reverter: o deslocamento nunca foi aplicado.")
            if not args.reverter and aplicada:
                sys.exit(f"Já aplicado em {aplicada['aplicada_em']}; aplicar de novo deslocaria 6h. Nada foi gravado.")

            antes = {}
            for tabela, (chave, ts, texto) in COLUNAS.items():
                colunas = ", ".join(chave + ts + texto)
                antes[tabela] = [
                    {k: _json(v) for k, v in linha.items()}
                    for linha in conn.execute(f"SELECT {colunas} FROM {tabela}").fetchall()
                ]

            amostra = conn.execute(
                "SELECT id, respondida_em FROM respostas ORDER BY respondida_em DESC LIMIT 3"
            ).fetchall()

            print(f"{'Revertendo (+3h)' if args.reverter else 'Deslocando (-3h)'} — "
                  f"{'GRAVANDO' if args.aplicar or args.reverter else 'simulação, nada é gravado'}")
            for tabela, (chave, ts, texto) in COLUNAS.items():
                for coluna in ts:
                    n = conn.execute(
                        f"UPDATE {tabela} SET {coluna} = {coluna} {sinal} INTERVAL '3 hours' WHERE {coluna} IS NOT NULL"
                    ).rowcount
                    print(f"  {tabela}.{coluna}: {n}")
                for coluna in texto:
                    n = conn.execute(
                        f"UPDATE {tabela} SET {coluna} = to_char({coluna}::timestamp {sinal} INTERVAL '3 hours', "
                        f"'YYYY-MM-DD\"T\"HH24:MI:SS.US') WHERE {coluna} IS NOT NULL"
                    ).rowcount
                    print(f"  {tabela}.{coluna}: {n}")

            depois = {
                linha["id"]: linha["respondida_em"]
                for linha in conn.execute(
                    f"SELECT id, respondida_em FROM respostas WHERE id IN ({', '.join('?' * len(amostra))})",
                    [linha["id"] for linha in amostra],
                ).fetchall()
            } if amostra else {}
            for linha in amostra:
                print(f"  exemplo: resposta {linha['id']}: {linha['respondida_em']} -> {depois[linha['id']]}")

            if args.reverter:
                conn.execute("DELETE FROM migracoes_dados WHERE nome = ?", (MARCA,))
            else:
                conn.execute(
                    "INSERT INTO migracoes_dados (nome, aplicada_em) VALUES (?, ?)", (MARCA, db.agora_br())
                )

            if not (args.aplicar or args.reverter):
                raise Simulacao

            destino = RAIZ / "backups" / f"fuso_brasilia_{'reverter' if args.reverter else 'aplicar'}_" \
                f"{db.agora_br():%Y%m%d_%H%M%S}.json"
            destino.parent.mkdir(exist_ok=True)
            destino.write_text(json.dumps(antes, ensure_ascii=False), encoding="utf-8")
            print(f"Valores anteriores salvos em {destino.relative_to(RAIZ)}")
    except Simulacao:
        print("Simulação desfeita. Para gravar: --aplicar (com backup_banco.py antes e a API parada).")


if __name__ == "__main__":
    main()
