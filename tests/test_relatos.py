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


def test_aluno_e_avisado_uma_vez_quando_o_relato_e_resolvido(usuario_teste, questao_teste):
    relato_id = db.relatar_erro_questao(usuario_teste, questao_teste, "Explicação")
    # Enquanto pendente, não há o que avisar.
    assert db.relatos_resolvidos_a_avisar(usuario_teste) == []

    db.resolver_relato(relato_id)
    a_avisar = db.relatos_resolvidos_a_avisar(usuario_teste)
    assert [r["id"] for r in a_avisar] == [relato_id]
    assert a_avisar[0]["questao_id"] == questao_teste

    db.marcar_relatos_avisados(usuario_teste)
    assert db.relatos_resolvidos_a_avisar(usuario_teste) == []


def test_aviso_nao_vaza_entre_usuarios(usuario_teste, questao_teste):
    relato_id = db.relatar_erro_questao(usuario_teste, questao_teste, "Imagem")
    db.resolver_relato(relato_id)
    # Outro usuário não vê o relato deste, nem o marca como visto.
    outro = db.criar_usuario(f"pytest_outro_{relato_id}@teste.local", "hash")
    try:
        assert db.relatos_resolvidos_a_avisar(outro) == []
        db.marcar_relatos_avisados(outro)
        assert [r["id"] for r in db.relatos_resolvidos_a_avisar(usuario_teste)] == [relato_id]
    finally:
        with db.get_conn() as conn:
            conn.execute("DELETE FROM usuarios WHERE id = ?", (outro,))
