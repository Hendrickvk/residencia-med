"""
Foto de perfil. O redimensionamento acontece no navegador, então o que o
servidor tem de garantir é o que o cliente não prova: tamanho dos bytes e
assinatura do arquivo. Um SVG com script dentro entrando como `image/png`
voltaria a ser servido da nossa origem.
"""

import base64
import uuid

from fastapi.testclient import TestClient

from api.main import app

import db

# PNG 2x2 de verdade — o mesmo do teste de cache da figura de questão.
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAEklEQVR4nGMUFBZlYGBgYgADAALSAD2bqWnMAAAAAElFTkSuQmCC"
)


def _envia(client, imagem: bytes, mime="image/png"):
    return client.put("/me/foto", json={"dados": base64.b64encode(imagem).decode(), "mime": mime})


def test_foto_sobe_volta_com_cache_e_sai():
    email = f"pytest_foto_{uuid.uuid4().hex[:10]}@teste.local"
    try:
        with TestClient(app) as client:
            assert client.post("/auth/signup", json={"email": email, "senha": "senha123"}).status_code == 201
            assert client.get("/me").json()["foto_versao"] is None
            assert client.get("/me/foto").status_code == 404

            versao = _envia(client, PNG).json()["foto_versao"]
            assert client.get("/me").json()["foto_versao"] == versao

            r = client.get("/me/foto")
            assert r.status_code == 200
            assert r.content == PNG
            assert r.headers["cache-control"] == "private, max-age=31536000, immutable"

            # Com o ETag na mão, os bytes não descem de novo.
            r304 = client.get("/me/foto", headers={"If-None-Match": r.headers["etag"]})
            assert r304.status_code == 304
            assert r304.content == b""

            assert client.delete("/me/foto").status_code == 204
            assert client.get("/me").json()["foto_versao"] is None
            assert client.get("/me/foto").status_code == 404
    finally:
        with db.get_conn() as conn:
            conn.execute("DELETE FROM usuarios WHERE email = ?", (email,))


def test_arquivo_que_mente_o_tipo_e_recusado():
    email = f"pytest_foto_{uuid.uuid4().hex[:10]}@teste.local"
    try:
        with TestClient(app) as client:
            assert client.post("/auth/signup", json={"email": email, "senha": "senha123"}).status_code == 201

            # SVG com script, declarado como PNG: a assinatura não bate.
            svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
            assert _envia(client, svg, "image/png").status_code == 400
            # E o tipo em si não está na lista.
            assert _envia(client, svg, "image/svg+xml").status_code == 400

            # Grande demais: recusado pelo tamanho decodificado.
            assert _envia(client, b"\x89PNG" + b"0" * db.FOTO_MAX_BYTES).status_code == 413

            assert client.get("/me").json()["foto_versao"] is None, "nada disso pode ter sido gravado"
    finally:
        with db.get_conn() as conn:
            conn.execute("DELETE FROM usuarios WHERE email = ?", (email,))
