"""Copia o banco inteiro para um arquivo, e confere que a cópia presta.

Os outros scripts deste diretório guardam em `backups/*.json` só as linhas que
cada operação toca — nenhum deles reconstrói o banco. Este reconstrói: são as
1 074 questões, as 79 imagens recortadas à mão dos cadernos e o histórico de
respostas e revisões dos alunos, que hoje só existem no Neon.

Rodar antes de qualquer operação em massa (importação, reclassificação,
correção de texto) e de vez em quando por hábito.

    python scripts/backup_banco.py
    python scripts/backup_banco.py --manter 10
    python scripts/backup_banco.py --espelho "D:/algum/lugar"
    python scripts/backup_banco.py --restaurar-instrucoes

`backups/` fica nesta máquina, que é o mesmo lugar de onde o banco é acessado:
um HD que morre leva o backup junto. `--espelho DIR` (ou a variável de
ambiente `BACKUP_ESPELHO`) copia o dump conferido para fora — uma pasta de
nuvem que sincroniza, um HD externo, um pendrive. A cópia é rotacionada igual
à daqui.

Restauração (não é automática de propósito — sobrescrever o banco tem de ser
um ato deliberado, digitado à mão):

    pg_restore --clean --if-exists --no-owner -d "$DATABASE_URL" <arquivo>
"""

import argparse
import glob
import os
import shutil
import subprocess
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO = os.path.join(RAIZ, "backups", "db")
# Pasta fora desta máquina (nuvem sincronizada, HD externo). Sem ela, o backup
# existe só onde está o risco.
ESPELHO = os.environ.get("BACKUP_ESPELHO", "")

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
    p.add_argument("--espelho", default=ESPELHO, metavar="DIR",
                   help="copia o dump conferido para fora desta máquina (padrão: $BACKUP_ESPELHO)")
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
    if not espelhar(arquivo, args.espelho, args.manter):
        return 1
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


def podar(manter, diretorio=DESTINO):
    arquivos = sorted(glob.glob(os.path.join(diretorio, "conduta_*.dump")))
    velhos = arquivos[:-manter] if manter > 0 else []
    for a in velhos:
        os.remove(a)
    if velhos:
        print("Removidos %d backup(s) antigo(s); %d mantido(s)." % (len(velhos), manter))


def espelhar(arquivo, diretorio, manter):
    """Copia o dump para fora da máquina. Devolve False só quando o destino foi
    pedido e a cópia não deu certo — não ter pedido não é erro."""
    if not diretorio:
        print("Sem espelho: o backup existe só nesta máquina "
              "(--espelho DIR ou BACKUP_ESPELHO resolve).")
        return True
    if not os.path.isdir(diretorio):
        print("Espelho %s não existe ou não é pasta — o dump local está salvo, "
              "mas não saiu daqui." % diretorio)
        return False
    fora = os.path.join(diretorio, os.path.basename(arquivo))
    try:
        shutil.copy2(arquivo, fora)
        # Pasta de nuvem escreve por cima enquanto sincroniza; conferir o
        # tamanho pega a cópia truncada, que é como isso falha na prática.
        copiado = os.path.getsize(fora)
    except OSError as erro:
        print("Falhou ao copiar para o espelho: %s" % erro)
        return False
    if copiado != os.path.getsize(arquivo):
        print("Cópia em %s saiu com %d bytes, o original tem %d — não confie nela."
              % (fora, copiado, os.path.getsize(arquivo)))
        return False
    print("Espelhado: %s (%.1f MB)" % (fora, copiado / 1e6))
    podar(manter, diretorio)
    return True


if __name__ == "__main__":
    sys.exit(main())
