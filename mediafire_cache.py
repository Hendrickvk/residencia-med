"""
Cache local dos arquivos de materiais importados do MediaFire.

O link salvo em `materiais.link_mediafire` normalmente é a página HTML do
arquivo (ex: https://www.mediafire.com/file/<quickkey>/<nome>/file), não um
link direto para o binário — é preciso abrir essa página e extrair o link
de download real (hospedado em algo como
https://download####.mediafire.com/...) antes de baixar o conteúdo.

O download é sempre feito sob demanda (botão "Baixar" por material) e nunca
automaticamente durante a sincronização, para não consumir espaço em disco
sem o usuário pedir — a pasta do MediaFire costuma ter vídeos de centenas
de MB cada.
"""

import os
import re
import unicodedata

import requests

import db

CACHE_DIR = os.path.join(os.path.dirname(__file__), "data", "materiais_cache")
TIMEOUT = 20
CHUNK_SIZE = 1024 * 256  # 256 KB por chunk, para não carregar o arquivo inteiro na memória

_PADRAO_LINK_DIRETO = re.compile(r'href="(https://download[0-9]*\.mediafire\.com/[^"]+)"')


class CacheError(Exception):
    pass


def _nome_arquivo_seguro(nome: str) -> str:
    """Remove acentos e caracteres inválidos em nomes de arquivo no Windows,
    mantendo o nome legível."""
    nome = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode("ascii")
    nome = re.sub(r'[<>:"/\\|?*]', "_", nome).strip()
    return nome or "arquivo"


def resolver_link_direto(link_pagina: str) -> str:
    """Abre a página do arquivo no MediaFire e extrai o link direto de
    download (hospedado no CDN de download, não em www.mediafire.com)."""
    try:
        resp = requests.get(link_pagina, timeout=TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise CacheError(f"Não consegui abrir a página do arquivo no MediaFire: {e}")

    m = _PADRAO_LINK_DIRETO.search(resp.text)
    if not m:
        raise CacheError(
            "Não encontrei o link direto de download nessa página. O MediaFire "
            "pode ter mudado o formato da página, ou o arquivo foi removido/"
            "ficou privado."
        )
    return m.group(1)


def baixar_material(material_id, on_progress=None):
    """Baixa o arquivo do material para `data/materiais_cache/` e grava o
    caminho local no banco. Retorna (arquivo_local_relativo, tamanho_bytes).

    `on_progress`, se fornecido, é chamado com (bytes_baixados, bytes_totais
    ou None) a cada chunk recebido.
    """
    material = db.obter_material(material_id)
    if material is None:
        raise CacheError("Material não encontrado.")

    link_pagina = material["link_mediafire"]
    if "mediafire.com/file/" in link_pagina:
        link_direto = resolver_link_direto(link_pagina)
    else:
        # já é (ou parece ser) um link direto — tenta baixar como está
        link_direto = link_pagina

    os.makedirs(CACHE_DIR, exist_ok=True)
    prefixo = material["mediafire_key"] or f"material{material_id}"
    nome_arquivo = _nome_arquivo_seguro(f"{prefixo}_{material['titulo']}")
    caminho_absoluto = os.path.join(CACHE_DIR, nome_arquivo)

    try:
        with requests.get(link_direto, stream=True, timeout=TIMEOUT) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("Content-Length") or 0) or None
            baixados = 0
            with open(caminho_absoluto, "wb") as f:
                for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                    if not chunk:
                        continue
                    f.write(chunk)
                    baixados += len(chunk)
                    if on_progress:
                        on_progress(baixados, total)
    except requests.RequestException as e:
        if os.path.exists(caminho_absoluto):
            os.remove(caminho_absoluto)
        raise CacheError(f"Falha ao baixar o arquivo: {e}")

    tamanho_bytes = os.path.getsize(caminho_absoluto)
    arquivo_local = os.path.relpath(caminho_absoluto, os.path.dirname(__file__))
    db.registrar_cache_material(material_id, arquivo_local, tamanho_bytes)
    return arquivo_local, tamanho_bytes


def caminho_absoluto(arquivo_local: str) -> str:
    return os.path.join(os.path.dirname(__file__), arquivo_local)


def esta_em_cache(material) -> bool:
    """Confere se o material realmente tem um arquivo em disco, não só o
    registro no banco. Em hospedagem com disco efêmero (ex: Streamlit
    Community Cloud), o contêiner pode reiniciar e apagar os arquivos
    baixados sem apagar o banco — nesse caso, autocorrige o registro (limpa
    o cache no banco) em vez de mostrar um botão "remover" pra um arquivo
    que já não existe."""
    if not material["arquivo_local"]:
        return False
    if os.path.exists(caminho_absoluto(material["arquivo_local"])):
        return True
    db.limpar_cache_material(int(material["id"]))
    return False


def limpar_todo_cache():
    """Remove todos os arquivos da pasta de cache local (não mexe no
    banco). Usado ao excluir todos os materiais de uma vez, pra não
    deixar arquivo órfão em disco."""
    if not os.path.isdir(CACHE_DIR):
        return
    for nome in os.listdir(CACHE_DIR):
        caminho = os.path.join(CACHE_DIR, nome)
        if os.path.isfile(caminho):
            os.remove(caminho)


def remover_cache(material_id):
    """Apaga o arquivo em cache (se existir) e limpa os campos no banco."""
    material = db.obter_material(material_id)
    if material and material["arquivo_local"]:
        caminho = caminho_absoluto(material["arquivo_local"])
        if os.path.exists(caminho):
            os.remove(caminho)
    db.limpar_cache_material(material_id)


def formatar_tamanho(tamanho_bytes) -> str:
    if not tamanho_bytes:
        return "-"
    valor = float(tamanho_bytes)
    for unidade in ["B", "KB", "MB", "GB"]:
        if valor < 1024 or unidade == "GB":
            return f"{valor:.1f} {unidade}"
        valor /= 1024
    return f"{valor:.1f} GB"
