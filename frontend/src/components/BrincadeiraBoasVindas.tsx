import { useEffect, useMemo, useRef, useState } from "react";
import { ALERTA, ROTEIRO, ROTEIRO_REPRISE, jaViu, marcarComoVista, normalizarNome } from "../lib/brincadeira";
import { BOTAO_PRIMARIO } from "../lib/estilos";
import { prefereMenosMovimento } from "../lib/movimento";

// O ritmo não vem da velocidade da letra, mas da pausa: sem respiro em ponto e
// em quebra de linha, o texto entra num jorro e parece apressado mesmo lento.
const MS_LETRA = 28;
const PAUSA_LINHA = 260;
const PAUSA_PONTO = 100;

// Instante em que cada caractere deve aparecer, pré-calculado por bloco.
function cronograma(texto: string): number[] {
  const tempos: number[] = [];
  let t = 0;
  for (const c of texto) {
    t += MS_LETRA;
    tempos.push(t);
    if (c === "\n") t += PAUSA_LINHA;
    else if (c === "." || c === "?" || c === ":") t += PAUSA_PONTO;
  }
  return tempos;
}

interface Entrada {
  tipo: "sistema" | "ela" | "veredito";
  texto: string;
}

// Sessão de boas-vindas que só aparece para uma convidada específica, uma vez
// por navegador (lib/brincadeira.ts). Para qualquer outra conta, não renderiza
// nada.
//
// É um terminal: o sistema digita, ela responde por menu numerado (clique ou
// tecla) e assina no fim. O histórico fica na tela e rola, como sessão de
// verdade — o que ela responde vira linha dela, e é isso que faz a coisa
// parecer conversa em vez de slideshow.
export function BrincadeiraBoasVindas({
  convidada,
  reprise = false,
  onEstado,
  onEfeito,
}: {
  // Já verificado pelo invólucro (useEhConvidada): `undefined` enquanto o
  // SHA-256 não respondeu.
  convidada: boolean | undefined;
  // Reprise pedida no menu da conta: o prelúdio muda e a sessão roda de novo,
  // mesmo já tendo sido vista neste navegador.
  reprise?: boolean;
  // Avisa o invólucro para ele segurar a página enquanto a sessão roda.
  onEstado?: (estado: "rodando" | "off") => void;
  // O que a sessão faz no app de verdade (por ora, escurecer o tema).
  onEfeito?: (efeito: "tema-escuro") => void;
}) {
  const roteiro = reprise ? ROTEIRO_REPRISE : ROTEIRO;
  const [aberto, setAberto] = useState(false);
  const [passo, setPasso] = useState(0);
  const [historico, setHistorico] = useState<Entrada[]>([]);
  // Bloco sendo digitado agora; null quando o terminal está esperando por ela.
  const [bloco, setBloco] = useState<string[] | null>(null);
  const [esperando, setEsperando] = useState<"menu" | "assinatura" | "fim" | null>(null);
  const [assinatura, setAssinatura] = useState("");
  const [tentativas, setTentativas] = useState(0);
  const [letras, setLetras] = useState(0);

  const texto = bloco ? bloco.join("\n") : "";
  const tempos = useMemo(() => cronograma(texto), [texto]);
  const completo = !bloco || letras >= texto.length;
  const atual = roteiro[passo];
  const fundo = useRef<HTMLDivElement>(null);
  const inicio = useRef(0);

  useEffect(() => {
    if (convidada === undefined) return;
    if (convidada && (reprise || !jaViu())) {
      setAberto(true);
      onEstado?.("rodando");
    } else {
      onEstado?.("off");
    }
    // Só o veredito da verificação de propósito: `onEstado` costuma vir como
    // função nova a cada render do invólucro, e incluí-la reabriria a sessão.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [convidada]);

  // Começa o primeiro bloco quando a sessão abre.
  useEffect(() => {
    if (aberto && bloco === null && historico.length === 0 && esperando === null) {
      digitar(roteiro[0].tipo === "fala" ? roteiro[0].linhas : []);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [aberto]);

  function digitar(linhas: string[]) {
    setBloco(linhas);
    inicio.current = performance.now();
    setLetras(prefereMenosMovimento() ? linhas.join("\n").length : 0);
  }

  // A posição vem do tempo decorrido, não de tiques: o Chrome estrangula
  // temporizador de aba escondida para um por segundo, e contando tique o
  // texto arrastaria para quem abrisse a aba e trocasse de janela.
  useEffect(() => {
    if (!aberto || completo) return;
    let quadro = requestAnimationFrame(function passoQuadro(agora) {
      const decorrido = agora - inicio.current;
      let n = 0;
      while (n < tempos.length && tempos[n] <= decorrido) n++;
      setLetras(n);
      quadro = requestAnimationFrame(passoQuadro);
    });
    return () => cancelAnimationFrame(quadro);
  }, [aberto, completo, tempos]);

  // Aba escondida pausa o requestAnimationFrame e a digitação congela onde
  // está. Na volta, o início é recalculado a partir do que já apareceu, para o
  // texto continuar do ponto em que parou em vez de saltar para o fim.
  const letrasVistas = useRef(0);
  letrasVistas.current = letras;
  useEffect(() => {
    function aoVoltar() {
      if (!document.hidden) {
        inicio.current = performance.now() - (tempos[letrasVistas.current - 1] ?? 0);
      }
    }
    document.addEventListener("visibilitychange", aoVoltar);
    return () => document.removeEventListener("visibilitychange", aoVoltar);
  }, [tempos]);

  // Terminado o bloco, ele desce para o histórico e o roteiro decide o que vem.
  useEffect(() => {
    if (!bloco || !completo) return;
    const linhas = bloco;
    const passoAtual = roteiro[passo];
    const timer = setTimeout(() => {
      setHistorico((h) => [...h, ...linhas.map((texto): Entrada => ({ tipo: "sistema", texto }))]);
      setBloco(null);
      // O efeito mexe no app de verdade (tema), então não pode derrubar a
      // sessão se falhar: sem este try a brincadeira travava no meio.
      if (passoAtual?.tipo === "fala" && passoAtual.efeito) {
        try {
          onEfeito?.(passoAtual.efeito);
        } catch {
          // Segue a piada mesmo sem o efeito.
        }
      }
      if (esperando === null) continuar();
    }, 420);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bloco, completo]);

  // Avança o roteiro a partir do passo seguinte ao atual.
  function continuar() {
    const proximo = passo + 1;
    if (proximo >= roteiro.length) {
      setEsperando("fim");
      return;
    }
    setPasso(proximo);
    const p = roteiro[proximo];
    if (p.tipo === "veredito") {
      setHistorico((h) => [...h, { tipo: "veredito", texto: ALERTA.veredito }]);
      setPasso(proximo + 1);
      const depois = roteiro[proximo + 1];
      if (depois && depois.tipo !== "veredito") digitar(depois.linhas);
      if (depois?.tipo === "escolha") setEsperando("menu");
      else if (depois?.tipo === "assinatura") setEsperando("assinatura");
      return;
    }
    digitar(p.linhas);
    if (p.tipo === "escolha") setEsperando("menu");
    else if (p.tipo === "assinatura") setEsperando("assinatura");
  }

  function escolher(indice: number) {
    if (atual.tipo !== "escolha") return;
    const opcao = atual.opcoes[indice];
    if (!opcao) return;
    setEsperando(null);
    setHistorico((h) => [...h, { tipo: "ela", texto: opcao.rotulo }]);
    digitar(opcao.resposta);
  }

  function assinar() {
    if (atual.tipo !== "assinatura") return;
    const digitado = assinatura.trim();
    if (!digitado) return;
    setHistorico((h) => [...h, { tipo: "ela", texto: digitado }]);
    setAssinatura("");
    const fecho = atual.resposta.map((l) => l.replace("{nome}", digitado.toLowerCase()));

    if (atual.aceitos.includes(normalizarNome(digitado))) {
      setEsperando(null);
      digitar([...atual.confirmacao, ...fecho]);
      return;
    }
    // `esperando` continua em "assinatura", então o campo volta sozinho quando
    // a recusa termina de ser digitada.
    //
    // Nome com recusa sob medida não gasta tentativa: são ovos de páscoa, ela
    // vai querer mostrar para alguém, e o sistema ceder no meio da piada
    // estragaria a piada. Quem escreve qualquer outra coisa segue na escada, e
    // a saída é sempre óbvia — assinar com o próprio nome.
    const especial = atual.especiais?.find((e) => e.quando.includes(normalizarNome(digitado)));
    if (especial) {
      digitar(especial.resposta);
      return;
    }
    const recusa = atual.recusas[tentativas];
    if (!recusa) {
      setEsperando(null);
      digitar([...atual.cedendo, ...fecho]);
      return;
    }
    setTentativas(tentativas + 1);
    digitar(recusa);
  }

  function encerrar() {
    // Fechar no meio também encerra: a piada não insiste.
    marcarComoVista();
    setAberto(false);
    onEstado?.("off");
  }

  useEffect(() => {
    if (!aberto) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        encerrar();
        return;
      }
      if (esperando === "menu" && atual.tipo === "escolha") {
        const n = Number(e.key);
        if (n >= 1 && n <= atual.opcoes.length) {
          e.preventDefault();
          escolher(n - 1);
        }
      }
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [aberto, esperando, atual]);

  // Mantém o fim da sessão à vista enquanto o texto cresce.
  useEffect(() => {
    const el = fundo.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [historico, letras, esperando]);

  if (!aberto) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 animate-desvanecer bg-black/70" aria-hidden="true" />
      {/* `alertdialog` e não `dialog`: é um aviso, e o leitor de tela anuncia o
          conteúdo inteiro em vez de esperar o foco chegar nele. */}
      <div
        role="alertdialog"
        aria-modal="true"
        aria-label={`${ALERTA.selo}: ${ALERTA.veredito}`}
        className="relative flex w-full max-w-lg flex-col gap-3 rounded-caso border-2 border-t1 bg-surface p-4 md:p-6"
      >
        <span className="rotulo text-t1">{ALERTA.selo}</span>

        <div ref={fundo} className="max-h-[52vh] overflow-y-auto">
          {historico.map((entrada, i) =>
            entrada.tipo === "veredito" ? (
              <p
                key={i}
                className="my-2 animate-entrar text-[27px] font-extrabold uppercase leading-none tracking-tight text-t1"
              >
                {entrada.texto}
                <span className="mt-2 block text-apoio font-normal normal-case tracking-normal text-muted">
                  {ALERTA.rodape}
                </span>
              </p>
            ) : (
              <p
                key={i}
                // `pl-3 -indent-3`: em tela estreita a linha quebra, e sem o
                // recuo pendente a continuação começava embaixo do ">", como
                // se fosse uma linha nova do log.
                className={`pl-3 -indent-3 text-apoio leading-relaxed ${
                  entrada.tipo === "ela" ? "text-ink" : "text-muted"
                }`}
              >
                {entrada.tipo === "ela" ? `$ ${entrada.texto}` : entrada.texto}
              </p>
            ),
          )}
          {/* Uma linha por parágrafo, e não um parágrafo com `\n`: o recuo
              pendente (`-indent-3`) só vale para a primeira linha de cada
              parágrafo, então no bloco único as linhas seguintes ficavam 12px
              à direita durante a digitação e saltavam para o lugar ao terminar,
              quando desciam para o histórico. */}
          {bloco &&
            texto
              .slice(0, letras)
              .split("\n")
              .map((linha, i, todas) => (
                <p key={i} className="pl-3 -indent-3 text-apoio leading-relaxed text-muted">
                  {linha}
                  {i === todas.length - 1 && !completo && (
                    <span className="animate-piscar text-ink">▍</span>
                  )}
                </p>
              ))}
        </div>

        {esperando === "menu" && completo && atual.tipo === "escolha" && (
          <ul className="flex animate-entrar flex-col gap-1">
            {atual.opcoes.map((opcao, i) => (
              <li key={opcao.rotulo}>
                <button
                  type="button"
                  onClick={() => escolher(i)}
                  className="w-full rounded-etq px-1 py-0.5 text-left text-apoio text-ink transition-colors duration-hover ease-brand hover:bg-ground"
                >
                  <span className="text-faint">[{i + 1}]</span> {opcao.rotulo}
                </button>
              </li>
            ))}
          </ul>
        )}

        {esperando === "assinatura" && completo && atual.tipo === "assinatura" && (
          <form
            className="flex animate-entrar items-center gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              assinar();
            }}
          >
            <label htmlFor="brincadeira-assinatura" className="text-apoio text-faint">
              $
            </label>
            <input
              id="brincadeira-assinatura"
              autoFocus
              maxLength={24}
              value={assinatura}
              onChange={(e) => setAssinatura(e.target.value)}
              placeholder={atual.rotulo}
              className="flex-1 border-b border-line bg-transparent pb-1 text-apoio text-ink outline-none placeholder:text-faint focus:border-ink"
            />
            <button type="submit" className="text-apoio font-semibold text-ink hover:underline">
              assinar
            </button>
          </form>
        )}

        {esperando === "fim" && (
          <div className="flex animate-entrar justify-end">
            <button type="button" onClick={encerrar} className={BOTAO_PRIMARIO}>
              {ALERTA.fim}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
