"""
Sincronização automática com uma pasta compartilhada do MediaFire.

O MediaFire expõe uma API pública de leitura (sem necessidade de login)
para pastas compartilhadas via link: `folder/get_content.php`. Usamos
isso para varrer toda a árvore de pastas de uma vez, em vez de cadastrar
cada link manualmente.

Estrutura esperada (conforme descrita pelo usuário):

    Pasta raiz compartilhada
    └── Cardiologia/  Cirurgia/  Dermatologia/   ...   <- viram ÁREAS
        └── Arritmias/  Insuficiência Cardíaca/  ...   <- viram SUBTÓPICOS
            └── apostila.pdf, aula1.mp4, ...            <- viram MATERIAIS
            └── Apostilas/  Videoaulas/  ...             <- subpastas por
                └── arquivo1.pdf, arquivo2.mp4              tipo (opcional)

A sincronização é idempotente: rodar de novo não duplica nada, graças à
`mediafire_key` (quickkey do arquivo) salva em cada material.
"""

import re
import time
import requests

import db

API_BASE = "https://www.mediafire.com/api/1.5/folder/get_content.php"
TIMEOUT = 20
MAX_TENTATIVAS = 3


class MediaFireError(Exception):
    pass


# ---------------------------------------------------------------------------
# Inferência do tipo de material a partir do nome do arquivo/pasta
# ---------------------------------------------------------------------------
_REGRAS_TIPO = [
    (re.compile(r"v[ií]deo[\s\-_]*apostila", re.IGNORECASE), "Vídeo Apostila"),
    (re.compile(r"b[ôo]nus", re.IGNORECASE), "Vídeo Bônus"),
    (re.compile(r"v[ií]deo[\s\-_]*aula|videoaula", re.IGNORECASE), "Videoaula"),
    (re.compile(r"apostila", re.IGNORECASE), "Apostila"),
    (re.compile(r"\.(mp4|mkv|avi|mov|webm)$", re.IGNORECASE), "Videoaula"),
    (re.compile(r"\.(pdf|doc|docx|ppt|pptx)$", re.IGNORECASE), "Apostila"),
]


def inferir_tipo(nome_arquivo: str, caminho_pastas):
    """Tenta descobrir o tipo do material olhando o nome do arquivo e, se
    não achar nada, os nomes das pastas do caminho (da mais específica
    para a mais geral)."""
    textos = [nome_arquivo] + list(reversed(caminho_pastas))
    for texto in textos:
        for padrao, tipo in _REGRAS_TIPO:
            if padrao.search(texto):
                return tipo
    return "Outro"


# ---------------------------------------------------------------------------
# Extração da folder_key a partir de um link ou chave crua
# ---------------------------------------------------------------------------
def extrair_folder_key(texto: str) -> str:
    texto = texto.strip()
    m = re.search(r"mediafire\.com/folder/([a-zA-Z0-9]+)", texto)
    if m:
        return m.group(1)
    if re.fullmatch(r"[a-zA-Z0-9]{10,20}", texto):
        return texto
    raise MediaFireError(
        "Não consegui identificar a chave da pasta a partir do texto informado. "
        "Cole o link completo (ex: https://www.mediafire.com/folder/abcd1234/Nome) "
        "ou apenas a folder_key."
    )


# ---------------------------------------------------------------------------
# Chamadas à API (com paginação e retry simples)
# ---------------------------------------------------------------------------
def _chamar_api(folder_key, content_type, chunk):
    params = {
        "response_format": "json",
        "folder_key": folder_key,
        "content_type": content_type,  # "folders" ou "files"
        "chunk": chunk,
        "order_by": "name",
        "order_direction": "asc",
    }
    ultimo_erro = None
    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            resp = requests.get(API_BASE, params=params, timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            return data["response"]
        except (requests.RequestException, ValueError, KeyError) as e:
            ultimo_erro = e
            time.sleep(1 * tentativa)
    raise MediaFireError(
        f"Falha ao consultar a pasta '{folder_key}' no MediaFire após "
        f"{MAX_TENTATIVAS} tentativas: {ultimo_erro}"
    )


def _listar_tudo(folder_key, content_type):
    """Percorre todas as páginas (chunks) e retorna a lista completa de
    'folders' ou 'files' de uma pasta."""
    itens = []
    chunk = 1
    while True:
        resposta = _chamar_api(folder_key, content_type, chunk)
        if resposta.get("result") != "Success":
            msg = resposta.get("message", "erro desconhecido")
            raise MediaFireError(f"MediaFire retornou erro para a pasta '{folder_key}': {msg}")

        conteudo = resposta.get("folder_content", {})
        itens.extend(conteudo.get(content_type, []) or [])

        if conteudo.get("more_chunks") != "yes":
            break
        chunk += 1
    return itens


# ---------------------------------------------------------------------------
# Varredura recursiva
# ---------------------------------------------------------------------------
def _processar_pasta(folder_key, nivel, area_id, subtopico_id, caminho, stats, on_progress):
    nome_caminho = " / ".join(caminho) if caminho else "(raiz)"
    if on_progress:
        on_progress(f"Explorando: {nome_caminho}")

    try:
        arquivos = _listar_tudo(folder_key, "files")
        subpastas = _listar_tudo(folder_key, "folders")
    except MediaFireError as e:
        stats["erros"].append(str(e))
        return

    # --- arquivos desta pasta viram materiais ---
    for f in arquivos:
        quickkey = f.get("quickkey")
        nome_arquivo = f.get("filename", "Arquivo sem nome")
        link = (f.get("links") or {}).get("normal_download") or (
            f"https://www.mediafire.com/file/{quickkey}/{nome_arquivo}" if quickkey else None
        )
        if not link or area_id is None:
            # arquivos soltos na raiz (fora de qualquer pasta de área) são ignorados,
            # já que não temos como saber a área/matéria deles
            continue

        tipo = inferir_tipo(nome_arquivo, caminho)
        titulo = nome_arquivo
        inserido = db.criar_material(area_id, subtopico_id, tipo, titulo, link, mediafire_key=quickkey)
        if inserido:
            stats["materiais_novos"] += 1
        else:
            stats["materiais_duplicados"] += 1

    # --- subpastas: papel depende do nível ---
    for pasta in subpastas:
        nome_pasta = pasta.get("name", "Sem nome")
        chave_pasta = pasta.get("folderkey")
        if not chave_pasta:
            continue

        if nivel == 0:
            # nível 0 = pasta raiz -> cada subpasta é uma ÁREA
            novo_area_id = db.obter_ou_criar_area(nome_pasta)
            stats["areas"].add(nome_pasta)
            _processar_pasta(
                chave_pasta, nivel=1, area_id=novo_area_id, subtopico_id=None,
                caminho=caminho + [nome_pasta], stats=stats, on_progress=on_progress,
            )
        elif nivel == 1:
            # nível 1 = dentro da área -> cada subpasta é um SUBTÓPICO/assunto
            novo_sub_id = db.obter_ou_criar_subtopico(area_id, nome_pasta)
            stats["subtopicos"].add((area_id, nome_pasta))
            _processar_pasta(
                chave_pasta, nivel=2, area_id=area_id, subtopico_id=novo_sub_id,
                caminho=caminho + [nome_pasta], stats=stats, on_progress=on_progress,
            )
        else:
            # nível >= 2 = pastas de organização por tipo (Apostilas, Videoaulas...)
            # não criam novas áreas/subtópicos, só continuam a varredura
            _processar_pasta(
                chave_pasta, nivel=nivel, area_id=area_id, subtopico_id=subtopico_id,
                caminho=caminho + [nome_pasta], stats=stats, on_progress=on_progress,
            )


def sincronizar_pasta_raiz(url_ou_key: str, on_progress=None):
    """
    Varre toda a árvore da pasta compartilhada do MediaFire e importa
    os materiais encontrados para o banco de dados.

    `on_progress`, se fornecido, é chamado com uma string a cada pasta
    visitada (útil para mostrar progresso na interface).

    Retorna um relatório (dict) com os números da sincronização.
    """
    folder_key = extrair_folder_key(url_ou_key)

    stats = {
        "areas": set(),
        "subtopicos": set(),
        "materiais_novos": 0,
        "materiais_duplicados": 0,
        "erros": [],
    }

    _processar_pasta(
        folder_key, nivel=0, area_id=None, subtopico_id=None,
        caminho=[], stats=stats, on_progress=on_progress,
    )

    return {
        "areas_criadas": len(stats["areas"]),
        "subtopicos_criados": len(stats["subtopicos"]),
        "materiais_novos": stats["materiais_novos"],
        "materiais_duplicados": stats["materiais_duplicados"],
        "erros": stats["erros"],
    }
