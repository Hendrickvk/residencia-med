"""
Cache da figura da questão. O que este teste prende é a economia: a mesma
imagem volta muitas vezes (a revisão espaçada traz a questão de novo) e ela
não pode descer de novo a cada aparição no celular da aluna.
"""

import base64
import uuid

from fastapi.testclient import TestClient

from api.main import app

import db

# PNG 2x2 de verdade, para o media_type fazer sentido.
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAEklEQVR4nGMUFBZlYGBgYgADAALSAD2bqWnMAAAAAElFTkSuQmCC"
)


def test_imagem_vem_com_etag_e_responde_304(questao_teste):
    with db.get_conn() as conn:
        conn.execute("UPDATE questoes SET imagem = ?, imagem_mime = ? WHERE id = ?",
                     (PNG, "image/png", questao_teste))
    email = f"pytest_img_{uuid.uuid4().hex[:10]}@teste.local"
    usuario_id = None
    try:
        with TestClient(app) as client:
            usuario_id = client.post("/auth/signup", json={"email": email, "senha": "senha123"}).json()["id"]

            r = client.get(f"/questoes/{questao_teste}/imagem")
            assert r.status_code == 200
            assert r.content == PNG
            assert r.headers["cache-control"] == "private, max-age=86400"
            etag = r.headers["etag"]
            assert etag.startswith('"') and etag.endswith('"')

            # Com o ETag na mão, o servidor não manda os bytes de novo.
            r = client.get(f"/questoes/{questao_teste}/imagem", headers={"If-None-Match": etag})
            assert r.status_code == 304
            assert r.content == b""
            assert r.headers["etag"] == etag

            # ETag do conteúdo: trocar a imagem invalida o cache na hora.
            with db.get_conn() as conn:
                conn.execute("UPDATE questoes SET imagem = ? WHERE id = ?", (PNG + b"\x00", questao_teste))
            r = client.get(f"/questoes/{questao_teste}/imagem", headers={"If-None-Match": etag})
            assert r.status_code == 200
            assert r.headers["etag"] != etag
    finally:
        if usuario_id:
            with db.get_conn() as conn:
                conn.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
