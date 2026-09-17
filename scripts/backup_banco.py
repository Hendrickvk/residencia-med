"""Copia o banco inteiro para um arquivo, e confere que a cópia presta.

Os outros scripts deste diretório guardam em `backups/*.json` só as linhas que
cada operação toca — nenhum deles reconstrói o banco. Este reconstrói: são as
1 074 questões, as 79 imagens recortadas à mão dos cadernos e o histórico de
respostas e revisões dos alunos, que hoje só existem no Neon.

Rodar antes de qualquer operação em massa (importação, reclassificação,
correção de texto) e de vez em quando por hábito.

    python scripts/backup_banco.py
    python scripts/backup_banco.py --manter 10
    python scripts/backup_banco.py --restaurar-instrucoes

Restauração (não é automática de propósito — sobrescrever o banco tem de ser
um ato deliberado, digitado à mão):

    pg_restore --clean --if-exists --no-owner -d "$DATABASE_URL" <arquivo>
"""

import argparse
import glob
import os
import subprocess
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO = os.path.join(RAIZ, "backups", "db")

# O Windows não põe o pg_dump no PATH por padrão.
CANDIDATOS = ["pg_dump"] + sorted(
    glob.glob(r"C:\Program Files\PostgreSQL\*\bin\pg_dump.exe"), reverse=True
)


def achar(programa):
    for caminho in CANDIDATOS:
        exe = caminho.replace("pg_dump", programa)
        try:
            subprocess.run([exe, "--version"], capture_output=True, check=True)
            return exe
        except (OSError, subprocess.CalledProcessError):
            continue
    return None


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--manter", type=int, default=7, help="quantos backups manter (padrão 7)")
    p.add_argument("--restaurar-instrucoes", action="store_true")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if args.restaurar_instrucoes:
        print(__doc__)
        return 0

    pg_dump = achar("pg_dump")
    if not pg_dump:
        print("pg_dump não encontrado. Instale o cliente do PostgreSQL ou ajuste CANDIDATOS.")
        return 1

    os.makedirs(DESTINO, exist_ok=True)
    arquivo = os.path.join(DESTINO, "conduta_%s.dump" % datetime.now().strftime("%Y%m%d_%H%M%S"))

    # Formato custom (-Fc): comprimido e restaurável seletivamente com
    # pg_restore. --no-owner porque o papel do Neon não existe em outro destino.
    cmd = [pg_dump, "--format=custom", "--no-owner", "--no-privileges",
           "--file", arquivo, db._database_url()]
    print("Copiando o banco... (pode levar um minuto, são ~20 MB de imagens)")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("pg_dump falhou:\n" + (r.stderr or "").strip())
        if os.path.exists(arquivo):
            os.remove(arquivo)
        return 1

    tamanho = os.path.getsize(arquivo)
    if not conferir(arquivo, tamanho):
        return 1

    print("  %s (%.1f MB)" % (arquivo, tamanho / 1e6))
    podar(args.manter)
    return 0


def conferir(arquivo, tamanho):
    """Um backup que ninguém conseguiu ler não é backup. Lê o índice do arquivo
    e confere que as tabelas que importam estão lá."""
    if tamanho < 100_000:
        print("Arquivo pequeno demais (%d bytes) — algo deu errado." % tamanho)
        return False

    pg_restore = achar("pg_restore")
    if not pg_restore:
        print("AVISO: pg_restore não encontrado, backup gravado mas NÃO conferido.")
        return True

    r = subprocess.run([pg_restore, "--list", arquivo], capture_output=True, text=True)
    if r.returncode != 0:
        print("O arquivo gravado não pôde ser lido pelo pg_restore:\n" + (r.stderr or "").strip())
        return False

    essenciais = ["questoes", "respostas", "revisao", "revisao_eventos", "usuarios"]
    faltando = [t for t in essenciais if (" %s " % t) not in r.stdout]
    if faltando:
        print("Backup incompleto, faltam tabelas: %s" % ", ".join(faltando))
        return False

    # Listar as tabelas só prova que o índice existe. Contar as linhas de dentro
    # do arquivo prova que os dados foram junto — já aconteceu de um dump sair
    # com o índice certo e conteúdo truncado.
    gravadas = contar_no_arquivo(pg_restore, arquivo, "questoes")
    with db.get_conn() as conn:
        vivas = conn.execute("SELECT count(*) AS n FROM questoes").fetchone()["n"]
    if gravadas != vivas:
        print("Backup com %s questões, mas o banco tem %s — não confie nele." % (gravadas, vivas))
        return False

    print("Conferido: legível, com as tabelas essenciais e as %d questões." % vivas)
    return True


def contar_no_arquivo(pg_restore, arquivo, tabela):
    """Linhas de uma tabela dentro do dump, sem precisar de servidor."""
    r = subprocess.run([pg_restore, "--data-only", "--table", tabela, "-f", "-", arquivo],
                       capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        return None
    linhas, dentro = 0, False
    for linha in r.stdout.splitlines():
        if linha.startswith("COPY "):
            dentro = True
        elif linha == "\\.":
            dentro = False
        elif dentro:
            linhas += 1
    return linhas


def podar(manter):
    arquivos = sorted(glob.glob(os.path.join(DESTINO, "conduta_*.dump")))
    velhos = arquivos[:-manter] if manter > 0 else []
    for a in velhos:
        os.remove(a)
    if velhos:
        print("Removidos %d backup(s) antigo(s); %d mantido(s)." % (len(velhos), manter))


if __name__ == "__main__":
    sys.exit(main())
