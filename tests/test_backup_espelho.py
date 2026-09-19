"""
O espelho do backup: o que este teste prende é que um espelho que não deu
certo não passa por bom. O dump local sempre existe; o risco é acreditar que
saiu da máquina quando não saiu.
"""

import importlib.util
import os

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
