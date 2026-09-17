"""Relatos de erro em questão (db.relatar_erro_questao e companhia)."""

import pytest

import db


def test_relato_aparece_como_pendente_e_some_ao_resolver(usuario_teste, questao_teste):
    antes = db.contar_relatos_pendentes()

    relato_id = db.relatar_erro_questao(
        usuario_teste, questao_teste, "Explicação", "  defende a letra errada  "
    )
    assert db.contar_relatos_pendentes() == antes + 1

    relato = next(r for r in db.listar_relatos() if r["id"] == relato_id)
    assert relato["questao_id"] == questao_teste
    assert relato["parte"] == "Explicação"
    # O comentário é gravado sem os espaços das pontas.
    assert relato["comentario"] == "defende a letra errada"
    assert relato["resolvido_em"] is None

    db.resolver_relato(relato_id)
    assert db.contar_relatos_pendentes() == antes
    assert all(r["id"] != relato_id for r in db.listar_relatos(pendentes=True))
    assert any(r["id"] == relato_id for r in db.listar_relatos(pendentes=False))


def test_comentario_vazio_vira_nulo(usuario_teste, questao_teste):
    relato_id = db.relatar_erro_questao(usuario_teste, questao_teste, "Imagem", "   ")
    relato = next(r for r in db.listar_relatos() if r["id"] == relato_id)
    assert relato["comentario"] is None
    db.resolver_relato(relato_id)


def test_parte_fora_da_lista_e_recusada(usuario_teste, questao_teste):
    # A lista é fechada porque é ela que diz onde mexer na questão; aceitar
    # texto livre aqui devolveria o problema que o relato existe para resolver.
    with pytest.raises(ValueError):
        db.relatar_erro_questao(usuario_teste, questao_teste, "Qualquer coisa")


def test_apagar_usuario_leva_os_relatos_junto(usuario_teste, questao_teste):
    relato_id = db.relatar_erro_questao(usuario_teste, questao_teste, "Gabarito")
    with db.get_conn() as conn:
        conn.execute("DELETE FROM usuarios WHERE id = ?", (usuario_teste,))
        sobrou = conn.execute(
            "SELECT COUNT(*) AS n FROM relatos_questao WHERE id = ?", (relato_id,)
        ).fetchone()["n"]
    assert sobrou == 0
