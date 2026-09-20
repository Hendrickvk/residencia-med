"""
O espelho do backup: o que este teste prende é que um espelho que não deu
certo não passa por bom. O dump local sempre existe; o risco é acreditar que
saiu da máquina quando não saiu.
"""

import importlib.util
import os
import subprocess

CAMINHO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "scripts", "backup_banco.py")
_spec = importlib.util.spec_from_file_location("backup_banco", CAMINHO)
backup_banco = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(backup_banco)


def test_sem_destino_nao_e_erro(tmp_path):
    dump = tmp_path / "conduta_20260101_000000.dump"
    dump.write_bytes(b"x" * 1000)
    assert backup_banco.espelhar(str(dump), "", 7) is True


def test_destino_inexistente_falha(tmp_path):
    dump = tmp_path / "conduta_20260101_000000.dump"
    dump.write_bytes(b"x" * 1000)
    assert backup_banco.espelhar(str(dump), str(tmp_path / "nao-existe"), 7) is False


def test_copia_chega_inteira_e_rotaciona(tmp_path):
    fora = tmp_path / "fora"
    fora.mkdir()
    # Três backups, mantendo dois: o mais antigo tem de sair do espelho também,
    # senão a pasta de nuvem cresce para sempre.
    for nome in ("conduta_20260101_000000.dump", "conduta_20260102_000000.dump",
                 "conduta_20260103_000000.dump"):
        dump = tmp_path / nome
        dump.write_bytes(b"x" * 1000)
        assert backup_banco.espelhar(str(dump), str(fora), 2) is True
        assert (fora / nome).read_bytes() == b"x" * 1000
    assert sorted(p.name for p in fora.glob("*.dump")) == [
        "conduta_20260102_000000.dump", "conduta_20260103_000000.dump"]


def test_empurra_o_espelho_com_um_commit_so(tmp_path):
    """O envio substitui o histórico. Testado contra um repositório local: o que
    importa aqui é a mecânica do orphan + force, não o GitHub."""
    remoto = tmp_path / "remoto.git"
    subprocess.run(["git", "init", "--bare", "-q", str(remoto)], check=True)
    espelho = tmp_path / "espelho"
    espelho.mkdir()
    subprocess.run(["git", "init", "-q", str(espelho)], check=True)
    for k, v in (("user.email", "teste@teste.local"), ("user.name", "pytest")):
        subprocess.run(["git", "-C", str(espelho), "config", k, v], check=True)
    subprocess.run(["git", "-C", str(espelho), "remote", "add", "origin", str(remoto)], check=True)

    def commits():
        r = subprocess.run(["git", "-C", str(remoto), "log", "--oneline", "main"],
                           capture_output=True, text=True)
        return [l for l in r.stdout.splitlines() if l]

    (espelho / "conduta_20260101_000000.dump").write_bytes(b"a" * 1000)
    assert backup_banco.empurrar(str(espelho)) is True
    assert len(commits()) == 1

    # Segundo envio: um dump novo, o antigo já rotacionado fora da pasta. O
    # remoto continua com um commit só e com exatamente o que está na pasta.
    (espelho / "conduta_20260101_000000.dump").unlink()
    (espelho / "conduta_20260102_000000.dump").write_bytes(b"b" * 1000)
    assert backup_banco.empurrar(str(espelho)) is True
    assert len(commits()) == 1
    arquivos = subprocess.run(["git", "-C", str(remoto), "ls-tree", "--name-only", "main"],
                              capture_output=True, text=True).stdout.split()
    assert arquivos == ["conduta_20260102_000000.dump"]


def test_empurrar_sem_remoto_falha(tmp_path):
    espelho = tmp_path / "sem-remoto"
    espelho.mkdir()
    subprocess.run(["git", "init", "-q", str(espelho)], check=True)
    assert backup_banco.empurrar(str(espelho)) is False
    # E fora de um repositório git também não inventa nada.
    assert backup_banco.empurrar(str(tmp_path)) is False
