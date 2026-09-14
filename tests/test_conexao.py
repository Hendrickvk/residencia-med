"""
O Neon fecha as conexões quando suspende o compute por inatividade. A
conexão que ficou parada no pool só descobria isso na próxima query, e a
primeira requisição depois de um tempo sem uso falhava com "connection
already closed". `db.get_conn` precisa trocar essa conexão por uma nova.
"""

import socket

import db


def test_get_conn_troca_conexao_morta_parada_no_pool():
    pool = db._get_pool()
    raw = pool.getconn()

    # Corta o socket por baixo do psycopg2, que continua achando a conexão
    # sã — igual a uma conexão que o servidor fechou enquanto estava parada.
    # (pg_terminate_backend não serve: a URL passa pelo pooler do Neon.)
    sock = socket.socket(fileno=raw.fileno())
    sock.shutdown(socket.SHUT_RDWR)
    sock.detach()

    db._ultimo_uso[id(raw)] = 0  # parada "há muito tempo"
    pool.putconn(raw)
    assert pool._pool == [raw], "a conexão morta precisa ser a próxima entregue pelo pool"

    with db.get_conn() as conn:
        assert conn.execute("SELECT 1 AS ok").fetchone()["ok"] == 1
