"""
Sincronização automática com uma pasta compartilhada do MediaFire.

O MediaFire expõe uma API pública de leitura (sem necessidade de login)
para pastas compartilhadas via link: `folder/get_content.php`. Usamos
isso para varrer toda a árvore de pastas de uma vez, em vez de cadastrar
cada link manualmente.

Estrutura esperada (conforme descrita pelo usuário):

    Pasta raiz compartilhada
    └── Cardiologia/  Cirurgia/  Dermatologia/   ...   <- ÁREA/ESPECIALIDADE
        └── Arritmias/  Insuficiência Cardíaca/  ...   <- viram SUBTÓPICOS
            └── apostila.pdf, aula1.mp4, ...            <- viram MATERIAIS
            └── Apostilas/  Videoaulas/  ...             <- subpastas por
                └── arquivo1.pdf, arquivo2.mp4              tipo (opcional)

As pastas do primeiro nível NÃO criam áreas: o nome é resolvido contra a
taxonomia fixa (`db.TAXONOMIA`, grande área > especialidade), então
"Aprenda Nefro - Gasometria" cai em Clínica Médica > Nefrologia. Pasta cujo
nome não corresponde a nada é pulada e aparece nos avisos do relatório.

A sincronização é idempotente: rodar de novo não duplica nada, graças à
`mediafire_key` (quickkey do arquivo) salva em cada material, e à `origem`
(nome original da pasta) salva em cada assunto.
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
# Nome de assunto a partir do nome da pasta do módulo
# ---------------------------------------------------------------------------
_PALAVRAS_MINUSCULAS = {"a", "o", "e", "de", "da", "do", "das", "dos", "em", "na", "no", "nas", "nos",
                        "ao", "aos", "com", "por", "para"}


def limpar_nome_assunto(nome_pasta: str) -> str:
    """'MEDCURSO - CAR 1 - ARRITMIAS CARDIACAS' -> 'Arritmias cardiacas'.
    Tira o nome do curso e o código do módulo, e desfaz o tudo-maiúsculo
    mantendo siglas curtas ('DM e dislipidemia')."""
    texto = re.sub(r"[_\s]+", " ", str(nome_pasta or "")).strip()
    partes = [p.strip() for p in re.split(r"\s-\s|\s-$|^-\s", texto) if p.strip()]
    uteis = [p for p in partes if not re.fullmatch(r"(?i)medcurso|[a-z]{2,8} ?\d{1,2}", p)]
    texto = " - ".join(uteis) or texto
    if texto.isupper():
        palavras = [
            p if len(p) <= 3 and p.lower() not in _PALAVRAS_MINUSCULAS else p.lower()
            for p in texto.split(" ")
        ]
        texto = " ".join(palavras)
        texto = texto[:1].upper() + texto[1:]
    return texto


def _palavras_significativas(texto):
    """'Vigilância de saúde' e 'Vigilância em saúde' -> 'vigilancia saude'."""
    return " ".join(p for p in db.normalizar_nome(texto).split() if p not in _PALAVRAS_MINUSCULAS)


def _assunto_da_pasta(area_id, nome_pasta_area, nome_pasta):
    """Assunto e especialidade de uma pasta de módulo dentro de uma pasta de
    área. Devolve (subtopico_id ou None, especialidade_id)."""
    nome_pasta = nome_pasta.strip()
    existente = db.obter_subtopico_por_origem(area_id, nome_pasta)
    if existente:
        # Já sincronizada antes: respeita o nome e a especialidade atuais,
        # mesmo que tenham sido corrigidos à mão depois.
        return existente["id"], existente["especialidade_id"]

    nome = limpar_nome_assunto(nome_pasta)
    area_nome, esp_nome = db.classificar_area_especialidade(nome_pasta_area, especialidade=nome)
    _, especialidade_id = db.resolver_area_especialidade(nome_pasta_area, especialidade=nome)

    modulo = db.classificar_nome_area(nome)
    if modulo and modulo[1] and modulo[1] == esp_nome:
        n_nome, n_esp = _palavras_significativas(nome), _palavras_significativas(esp_nome)
        if n_esp.startswith(n_nome) or n_nome.startswith(n_esp):
            # A pasta é a própria especialidade ("MEDCURSO - PSIQUIATRIA"):
            # os arquivos ficam na especialidade, sem um assunto repetindo o nome.
            return None, especialidade_id

    sub_id = db.criar_subtopico_de_origem(area_id, nome, origem=nome_pasta, especialidade_id=especialidade_id)
    return sub_id, especialidade_id


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
def _processar_pasta(folder_key, nivel, area_id, subtopico_id, caminho, stats, on_progress,
                     especialidade_id=None):
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
        inserido = db.criar_material(
            area_id, subtopico_id, tipo, titulo, link,
            mediafire_key=quickkey, especialidade_id=especialidade_id,
        )
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
            # nível 0 = pasta raiz -> cada subpasta é uma grande área ou especialidade
            ids = db.resolver_area_especialidade(nome_pasta)
            if ids is None:
                stats["erros"].append(
                    f"Pasta '{nome_pasta}' ignorada: o nome não corresponde a nenhuma grande área "
                    "ou especialidade. Renomeie a pasta (ex: 'Nefrologia') e sincronize de novo."
                )
                continue
            novo_area_id, nova_esp_id = ids
            stats["areas"].add(nome_pasta)
            _processar_pasta(
                chave_pasta, nivel=1, area_id=novo_area_id, subtopico_id=None,
                caminho=caminho + [nome_pasta], stats=stats, on_progress=on_progress,
                especialidade_id=nova_esp_id,
            )
        elif nivel == 1 and inferir_tipo(nome_pasta, []) == "Outro":
            # nível 1 = dentro da área -> cada subpasta é um módulo/assunto
            novo_sub_id, esp_id = _assunto_da_pasta(area_id, caminho[0], nome_pasta)
            if novo_sub_id is not None:
                stats["subtopicos"].add((area_id, nome_pasta))
            _processar_pasta(
                chave_pasta, nivel=2, area_id=area_id, subtopico_id=novo_sub_id,
                caminho=caminho + [nome_pasta], stats=stats, on_progress=on_progress,
                especialidade_id=esp_id or especialidade_id,
            )
        else:
            # nível >= 2 = pastas de organização por tipo (Apostilas, Videoaulas...),
            # ou uma dessas direto na área: não criam assunto, só continuam a varredura
            _processar_pasta(
                chave_pasta, nivel=max(nivel, 2), area_id=area_id, subtopico_id=subtopico_id,
                caminho=caminho + [nome_pasta], stats=stats, on_progress=on_progress,
                especialidade_id=especialidade_id,
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
