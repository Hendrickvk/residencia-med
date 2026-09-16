"""
Importa uma prova inteira para o banco, a partir de um JSON já montado.

Simula por padrão; `--aplicar` grava tudo numa transação e salva backup em
`backups/`. Resolve área, especialidade e tema pelos nomes (db.TAXONOMIA e
db.TEMAS) e recusa nome desconhecido, como manda o CLAUDE.md — nunca cria área.

Formato do JSON:

    {
      "banca": "REVALIDA", "ano": 2021, "edicao": "2021",
      "questoes": [
        {"numero_prova": 1, "area": "...", "especialidade": "...", "tema": "...",
         "tipo_pergunta": "Conduta", "enunciado": "...",
         "alternativas": {"A": "...", "B": "...", "C": "...", "D": "..."},
         "resposta_correta": "B", "explicacao": "...",
         "imagem": "caminho/opcional.png"}
      ]
    }

Uso:
    python scripts/importar_prova.py prova.json            # simula
    python scripts/importar_prova.py prova.json --aplicar  # grava
"""

import argparse
import datetime
import json
import mimetypes
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db  # noqa: E402

PASTA_BACKUP = "backups"


def _chave_duplicata(banca, ano, enunciado):
    """Banca + ano + começo do enunciado, sem acento nem pontuação: é assim que
    as importações anteriores acharam questão repetida entre cadernos."""
    texto = unicodedata.normalize("NFKD", (enunciado or "").lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return (banca or "").upper(), ano, re.sub(r"[^a-z0-9 ]", "", texto)[:90]


def validar(prova):
    """Confere tudo antes de tocar no banco. Devolve (questões prontas, erros)."""
    banca, ano, edicao = prova.get("banca"), prova.get("ano"), prova.get("edicao")
    erros = []
    if not banca or not ano or not edicao:
        erros.append("JSON sem banca, ano ou edicao")
        return [], erros

    with db.get_conn() as conn:
        existentes = conn.execute("SELECT banca, ano, enunciado FROM questoes").fetchall()
        ja_no_banco = {_chave_duplicata(q["banca"], q["ano"], q["enunciado"]) for q in existentes}
        numeros_da_edicao = {
            linha["numero_prova"]
            for linha in conn.execute(
                "SELECT numero_prova FROM questoes_provas WHERE banca = ? AND edicao = ?", (banca, edicao)
            ).fetchall()
        }

    prontas, numeros_vistos = [], set()
    for bruta in prova.get("questoes", []):
        numero = bruta.get("numero_prova")
        rotulo = f"questão {numero}"
        try:
            resolvido = db.resolver_area_especialidade(bruta["area"], bruta["especialidade"])
            if resolvido is None:
                raise ValueError(f"área ou especialidade desconhecida: {bruta['area']} / {bruta['especialidade']}")
            area_id, especialidade_id = resolvido
            # obter_tema devolve a linha do tema, não o id.
            tema = db.obter_tema(area_id, bruta["tema"])
            if tema is None:
                raise ValueError(f"tema desconhecido: {bruta['tema']}")
            tema_id = tema["id"]
        except Exception as e:
            erros.append(f"{rotulo}: {e}")
            continue

        alternativas = bruta.get("alternativas") or {}
        if bruta.get("tipo_pergunta") not in db.TIPOS_PERGUNTA:
            erros.append(f"{rotulo}: tipo_pergunta inválido ({bruta.get('tipo_pergunta')})")
        if len(alternativas) < 2:
            erros.append(f"{rotulo}: menos de 2 alternativas")
        if bruta.get("resposta_correta") not in alternativas:
            erros.append(f"{rotulo}: resposta_correta fora das alternativas")
        if not (bruta.get("explicacao") or "").strip():
            erros.append(f"{rotulo}: sem explicação")
        if numero in numeros_vistos or numero in numeros_da_edicao:
            erros.append(f"{rotulo}: número repetido nesta edição")
        numeros_vistos.add(numero)
        if _chave_duplicata(banca, ano, bruta.get("enunciado")) in ja_no_banco:
            erros.append(f"{rotulo}: enunciado já existe no banco")
        imagem = bruta.get("imagem")
        if imagem and not os.path.exists(imagem):
            erros.append(f"{rotulo}: imagem não encontrada ({imagem})")

        prontas.append({**bruta, "area_id": area_id, "especialidade_id": especialidade_id, "tema_id": tema_id})
    return prontas, erros


def resumir(prova, prontas):
    print(f"{prova['banca']} {prova['edicao']} (ano {prova['ano']}): {len(prontas)} questões")
    for chave in ("area", "tipo_pergunta"):
        contagem = {}
        for q in prontas:
            contagem[q[chave]] = contagem.get(q[chave], 0) + 1
        print(f"  por {chave}: " + ", ".join(f"{k} {v}" for k, v in sorted(contagem.items())))
    com_imagem = [q["numero_prova"] for q in prontas if q.get("imagem")]
    print(f"  com imagem: {com_imagem or 'nenhuma'}")


def aplicar(prova, prontas):
    banca, ano, edicao = prova["banca"], prova["ano"], prova["edicao"]
    agora = datetime.datetime.now().isoformat()
    inseridas = []
    with db.get_conn() as conn:  # uma transação: ou entra a prova inteira, ou nada
        c = conn.cursor()
        for q in prontas:
            c.execute("""
                INSERT INTO questoes
                    (area_id, especialidade_id, subtopico_id, enunciado, alternativas, resposta_correta,
                     explicacao, banca, ano, edicao, numero_prova, tipo_pergunta, criada_em)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                q["area_id"], q["especialidade_id"], q["tema_id"], q["enunciado"],
                json.dumps(q["alternativas"], ensure_ascii=False), q["resposta_correta"],
                q["explicacao"], banca, ano, edicao, q["numero_prova"], q["tipo_pergunta"], agora,
            ))
            questao_id = c.lastrowid
            c.execute(
                "INSERT INTO questoes_provas (questao_id, banca, edicao, numero_prova) VALUES (?, ?, ?, ?)",
                (questao_id, banca, edicao, q["numero_prova"]),
            )
            if q.get("imagem"):
                with open(q["imagem"], "rb") as arquivo:
                    dados = arquivo.read()
                mime = mimetypes.guess_type(q["imagem"])[0] or "image/png"
                c.execute("UPDATE questoes SET imagem = ?, imagem_mime = ? WHERE id = ?",
                          (psycopg2_binario(dados), mime, questao_id))
            inseridas.append({"id": questao_id, "numero_prova": q["numero_prova"]})

    os.makedirs(PASTA_BACKUP, exist_ok=True)
    caminho = os.path.join(
        PASTA_BACKUP,
        f"importacao_{banca.lower()}_{edicao.replace('/', '-')}_{datetime.datetime.now():%Y%m%d_%H%M%S}.json",
    )
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump({"banca": banca, "edicao": edicao, "ano": ano, "questoes": inseridas},
                  arquivo, ensure_ascii=False, indent=1)
    print(f"Gravadas {len(inseridas)} questões. Ids em {caminho}")


def psycopg2_binario(dados):
    import psycopg2
    return psycopg2.Binary(dados)


def main():
    parser = argparse.ArgumentParser(description="Importa uma prova inteira a partir de um JSON.")
    parser.add_argument("json", help="arquivo com a prova montada")
    parser.add_argument("--aplicar", action="store_true", help="grava no banco (sem isso, só simula)")
    args = parser.parse_args()

    with open(args.json, encoding="utf-8") as arquivo:
        prova = json.load(arquivo)
    prontas, erros = validar(prova)
    resumir(prova, prontas)
    if erros:
        print(f"\n{len(erros)} problema(s):")
        for erro in erros[:30]:
            print("  -", erro)
        print("Nada foi gravado.")
        sys.exit(1)
    if not args.aplicar:
        print("\nSimulação: nada gravado. Rode com --aplicar para gravar.")
        return
    aplicar(prova, prontas)


if __name__ == "__main__":
    main()
