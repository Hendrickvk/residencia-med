"""Procura explicações que não defendem a alternativa oficial.

A checagem anterior olhava se a explicação citava a *letra* correta, e não pegou
o caso mais grave achado na revisão de 2026-09-16 (USP 2026 Q22): a explicação
argumentava a favor de outra alternativa sem nomear letra nenhuma. A regra aqui
olha o *conteúdo* da alternativa correta:

  MUDA    a explicação não menciona nenhuma das palavras que distinguem a
          alternativa correta das outras três.

Uma segunda regra foi tentada e descartada: marcar quando todas as frases que
citam a alternativa correta a negam. Ela pegava a Q22, mas rendeu 6 falsos
positivos e nenhum acerto no banco inteiro, porque prosa clínica está cheia de
negação que descreve ("não invasivo", "não caseoso", "não reagente") ou que
descarta o distrator na mesma frase em que afirma o gabarito. A Q22 é pega pela
regra MUDA de qualquer forma. Se for tentar de novo, o problema é distinguir
negação de descarte da de descritor — não adianta só apertar a janela.

Precisão medida em 2026-09-16, no banco de 1 074 questões: 26 suspeitas, quase
todas falso positivo por sinônimo — a explicação diz "soro fisiológico" onde a
alternativa diz "cloreto de sódio 0,9%", ou "destrói os precursores eritroides"
onde ela diz "supressão da eritropoiese medular". Ou seja: **não use isto como
auditoria do banco**, que hoje devolveria só ruído. O uso que se paga é como
rede de segurança logo depois de escrever explicações novas — importou uma
prova, rodou nas 90 daquela edição e leu as duas ou três marcadas.

E o limite maior: isto **não vê** raciocínio clínico errado defendendo a letra
certa, que foi a maioria dos problemas achados lendo à mão.

    python scripts/auditar_explicacoes.py                    # banco inteiro
    python scripts/auditar_explicacoes.py --banca USP --edicao 2026
"""

import argparse
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db

# Palavras comuns demais para identificar uma alternativa.
VAZIAS = {
    "para", "pelo", "pela", "pelos", "pelas", "como", "mais", "menos", "entre",
    "sobre", "esse", "essa", "este", "esta", "aquele", "aquela", "quando",
    "porque", "todos", "todas", "outro", "outra", "outros", "outras", "seus",
    "suas", "nao", "sem", "com", "dos", "das", "nos", "nas", "por", "que",
    "uma", "uns", "umas", "apos", "ante", "cada", "deve", "devem", "pode",
    "podem", "fazer", "realizar", "solicitar", "indicar", "iniciar", "manter",
    "paciente", "pacientes", "seja", "sendo", "seria", "antes", "mesmo",
    "medidas", "caso", "casos",
}


def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def termos_distintivos(alternativas, letra):
    """Palavras da alternativa `letra` que não aparecem nas outras."""
    def palavras(t):
        return {p for p in re.findall(r"[a-z]{4,}", normalizar(t)) if p not in VAZIAS}

    minhas = palavras(alternativas[letra])
    outras = set()
    for l, t in alternativas.items():
        if l != letra:
            outras |= palavras(t)
    return minhas - outras


def auditar(q):
    """Devolve (codigo, detalhe) ou None se a explicação passa."""
    explicacao = q["explicacao"] or ""
    if not explicacao.strip():
        return ("SEM_EXPLICACAO", "")
    alternativas = db.json.loads(q["alternativas"])
    letra = q["resposta_correta"]
    if letra not in alternativas:
        return ("GABARITO_INVALIDO", letra)
    # Alternativa-imagem ("Imagem B.") não tem conteúdo com que comparar.
    if alternativas[letra].strip().lower().rstrip(".").startswith("imagem "):
        return None

    # Com um termo só, e curto, o sinal é fraco demais: sai falso positivo por
    # sinônimo ("dosagem" x "dosar").
    termos = {t for t in termos_distintivos(alternativas, letra) if len(t) >= 5}
    if len(termos) < 2:
        return None

    alvo = normalizar(explicacao)
    if not any(t in alvo for t in termos):
        return ("MUDA", "termos ausentes: " + ", ".join(sorted(termos)[:6]))
    return None


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--banca")
    p.add_argument("--edicao")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if args.banca and args.edicao:
        ids = db.ids_questoes_da_edicao(args.banca, args.edicao)
    else:
        with db.get_conn() as conn:
            ids = [r["id"] for r in conn.execute("SELECT id FROM questoes ORDER BY id").fetchall()]

    achados = []
    for qid in ids:
        q = db.obter_questao(qid)
        r = auditar(q)
        if r is not None:
            achados.append((q, *r))

    for q, codigo, detalhe in achados:
        prova = " ".join(str(x) for x in (q["banca"], q["edicao"]) if x)
        print("[%s] id %s — %s, questão %s — gabarito %s: %s" % (
            codigo, q["id"], prova, q["numero_prova"], q["resposta_correta"],
            alternativa_curta(q)))
        if detalhe:
            print("    %s" % detalhe)

    print("\n%d questões analisadas, %d suspeita(s)." % (len(ids), len(achados)))


def alternativa_curta(q):
    try:
        return db.json.loads(q["alternativas"])[q["resposta_correta"]][:70]
    except Exception:
        return "?"


if __name__ == "__main__":
    main()
