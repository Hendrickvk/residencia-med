import { X } from "lucide-react";
import { useEffect, useRef, useState, type CSSProperties, type KeyboardEvent } from "react";
import { prefereMenosMovimento, usePresenca } from "../lib/movimento";
import { FAMILIAS, partes, TOM_DA_FAMILIA, type Familia } from "../lib/paleta";

// Geometria do disco: os oito tons num anel em volta da cor tocada.
const RAIO = 52; // do centro do disco ao centro de cada tom
const TOM = 32; // lado de cada tom
const DISCO = 2 * (RAIO + TOM / 2 + 8);
const FOLGA = 8; // distância mínima entre o disco e a borda da janela
const ESCALONAMENTO_MS = 30;

interface Abertura {
  chave: string;
  // Quanto o disco sai do centro da cor tocada para caber na janela.
  desvio: { x: number; y: number };
}

// Centro que cabe na janela, menos o centro de verdade.
function desvioParaCaber(centro: number, tela: number): number {
  const margem = DISCO / 2 + FOLGA;
  const alvo = tela < 2 * margem ? tela / 2 : Math.min(Math.max(centro, margem), tela - margem);
  return alvo - centro;
}

// Seletor de cor em duas camadas (pedido do usuário, 2026-09-24): a fileira
// mostra as dez famílias, e tocar numa delas abre em volta dela um disco com
// os oito tons — o mais claro no alto, escurecendo em sentido horário.
//
// Movimento (skills `animate` e `emil-design-eng`, DESIGN_TRIAGEM.md §3): os
// tons saem de trás da cor tocada e voltam para ela ao fechar, que é o que diz
// de onde vieram. Só transform e opacity; transição e não keyframe, então
// reabrir no meio do fechamento retoma de onde parou; `suave` na entrada,
// escalonada em 30 ms, e saída mais curta e sem escalonar. Com menos movimento
// pedido, a regra global do theme.css já zera as durações.
export function SeletorCor({
  valor,
  onChange,
  tamanho = 36,
}: {
  /** Chave já normalizada (`normalizarCor`). */
  valor: string;
  onChange: (chave: string) => void;
  /** Lado do círculo de cada família, em pixels. */
  tamanho?: number;
}) {
  const atual = partes(valor);
  const [aberta, setAberta] = useState<Abertura | null>(null);
  // O que está desenhado no disco: continua o mesmo durante a saída, quando
  // `aberta` já é null.
  const [noDisco, setNoDisco] = useState<Abertura | null>(null);
  if (aberta && aberta !== noDisco) setNoDisco(aberta);
  const { montado, saindo } = usePresenca(aberta !== null);
  // Cor recém-escolhida: remonta o miolo do círculo, que "carimba" como a
  // letra da alternativa no Praticar. Null no carregamento, para nada pular
  // sozinho.
  const [carimbo, setCarimbo] = useState<string | null>(null);
  const gatilhos = useRef(new Map<string, HTMLButtonElement>());

  function alternar(chave: string, botao: HTMLButtonElement) {
    if (aberta?.chave === chave) {
      setAberta(null);
      return;
    }
    const r = botao.getBoundingClientRect();
    setAberta({
      chave,
      desvio: {
        x: desvioParaCaber(r.left + r.width / 2, window.innerWidth),
        y: desvioParaCaber(r.top + r.height / 2, window.innerHeight),
      },
    });
  }

  function fechar(devolverFoco: boolean) {
    if (devolverFoco && aberta) gatilhos.current.get(aberta.chave)?.focus();
    setAberta(null);
  }

  function escolher(chave: string) {
    onChange(chave);
    setCarimbo(chave);
    fechar(true);
  }

  return (
    <div className="flex flex-wrap gap-2.5">
      {FAMILIAS.map((familia) => {
        const escolhida = atual?.familia.chave === familia.chave;
        const tom = familia.tons[escolhida ? atual.indice : TOM_DA_FAMILIA];
        const carimbando = escolhida && carimbo === valor;
        return (
          <span key={familia.chave} className="relative">
            <button
              ref={(el) => {
                if (el) gatilhos.current.set(familia.chave, el);
                else gatilhos.current.delete(familia.chave);
              }}
              type="button"
              onClick={(e) => alternar(familia.chave, e.currentTarget)}
              aria-expanded={aberta?.chave === familia.chave}
              aria-label={escolhida ? `${familia.nome}, tom ${atual.indice + 1} de 8, escolhida` : familia.nome}
              style={{ width: tamanho, height: tamanho }}
              // A escolhida ganha anel de tinta, não borda colorida: a cor do
              // círculo já é a informação, e um segundo tom competiria.
              className={`block rounded-pill transition-transform duration-hover ease-brand active:scale-[0.96] ${
                escolhida ? "ring-2 ring-ink ring-offset-2 ring-offset-surface" : ""
              }`}
            >
              <span
                key={carimbando ? carimbo : "base"}
                className={`block h-full w-full rounded-pill border border-black/15 dark:border-white/15 transition-colors duration-toggle ease-brand ${
                  carimbando ? "animate-marcar" : ""
                }`}
                style={{ backgroundColor: tom.hex }}
              />
            </button>
            {montado && noDisco?.chave === familia.chave && (
              <Disco
                familia={familia}
                valor={valor}
                desvio={noDisco.desvio}
                saindo={saindo}
                tamanho={tamanho}
                onEscolher={escolher}
                onFechar={fechar}
              />
            )}
          </span>
        );
      })}
    </div>
  );
}

function Disco({
  familia,
  valor,
  desvio,
  saindo,
  tamanho,
  onEscolher,
  onFechar,
}: {
  familia: Familia;
  valor: string;
  desvio: Abertura["desvio"];
  saindo: boolean;
  tamanho: number;
  onEscolher: (chave: string) => void;
  onFechar: (devolverFoco: boolean) => void;
}) {
  // A cor tocada é o irmão logo antes do disco, no mesmo invólucro
  // (`caixa.current.previousElementSibling`).
  const caixa = useRef<HTMLDivElement>(null);
  const tons = useRef<(HTMLButtonElement | null)[]>([]);
  // O pai cria o `onFechar` a cada render; numa ref, o ouvinte de toque fora
  // não precisa ser refeito a cada vez.
  const fechar = useRef(onFechar);
  fechar.current = onFechar;
  const escolhido = partes(valor);
  const indiceEscolhido = escolhido?.familia.chave === familia.chave ? escolhido.indice : -1;
  const miolo = familia.tons[indiceEscolhido >= 0 ? indiceEscolhido : TOM_DA_FAMILIA];
  const escalonar = !prefereMenosMovimento();
  // Aberto é o estado normal do CSS (`.disco-cor`, no theme.css); a entrada
  // parte do `@starting-style` e a saída, do `data-saindo`. Nada espera
  // quadro: numa aba que se declara escondida o `requestAnimationFrame` não
  // roda, e o disco ficava montado e invisível.

  // Foco no tom escolhido, ou no primeiro: é daí que as setas andam.
  useEffect(() => {
    tons.current[Math.max(indiceEscolhido, 0)]?.focus();
    // Só ao abrir: trocar de tom fecha o disco.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Toque fora fecha. Por `pointerdown`, e não só pela perda de foco: o Safari
  // não dá foco a botão tocado, então tocar fora não tiraria o foco de nada.
  useEffect(() => {
    function fora(e: PointerEvent) {
      const alvo = e.target as Node;
      const disco = caixa.current;
      if (!disco?.contains(alvo) && !disco?.previousElementSibling?.contains(alvo)) fechar.current(false);
    }
    document.addEventListener("pointerdown", fora);
    return () => document.removeEventListener("pointerdown", fora);
  }, []);

  function teclas(e: KeyboardEvent) {
    const i = tons.current.findIndex((t) => t === document.activeElement);
    const ir = (n: number) => {
      e.preventDefault();
      tons.current[(n + 8) % 8]?.focus();
    };
    if (e.key === "Escape") {
      // Sem isto o Esc fecharia também o diálogo em volta (o da pasta).
      e.stopPropagation();
      onFechar(true);
    } else if (e.key === "ArrowRight" || e.key === "ArrowDown") ir(i < 0 ? 0 : i + 1);
    else if (e.key === "ArrowLeft" || e.key === "ArrowUp") ir(i < 0 ? 7 : i - 1);
    else if (e.key === "Home") ir(0);
    else if (e.key === "End") ir(7);
  }

  const entrada = saindo ? "duration-hover ease-brand" : "duration-toggle ease-suave";
  // Recolhido, cada tom fica atrás da cor tocada.
  const recolhido = `translate(${-desvio.x}px, ${-desvio.y}px) scale(0.9)`;
  return (
    <div
      ref={caixa}
      role="group"
      aria-label={`Tons de ${familia.nome}`}
      // Focável por código: tocar no fundo do disco não pode contar como sair.
      tabIndex={-1}
      onKeyDown={teclas}
      onBlur={(e) => {
        const para = e.relatedTarget as Node | null;
        if (!caixa.current?.contains(para) && para !== caixa.current?.previousElementSibling) onFechar(false);
      }}
      data-saindo={saindo || undefined}
      className={`disco-cor absolute left-1/2 top-1/2 z-30 rounded-pill border border-line bg-surface outline-none transition-[opacity,transform] ${entrada} ${
        saindo ? "pointer-events-none" : ""
      }`}
      style={{
        width: DISCO,
        height: DISCO,
        marginLeft: desvio.x - DISCO / 2,
        marginTop: desvio.y - DISCO / 2,
        // Cresce a partir da cor tocada, mesmo quando foi desviado para caber.
        transformOrigin: `${DISCO / 2 - desvio.x}px ${DISCO / 2 - desvio.y}px`,
      }}
    >
      {familia.tons.map((tom, i) => {
        const angulo = (i * Math.PI) / 4;
        return (
          <span
            key={tom.hex}
            className={`tom-cor absolute left-1/2 top-1/2 transition-[opacity,transform] ${entrada}`}
            style={
              {
                width: TOM,
                height: TOM,
                marginLeft: -TOM / 2,
                marginTop: -TOM / 2,
                // Por variável, e não `transform` inline: estilo inline venceria
                // o `@starting-style`, e a entrada não aconteceria.
                "--lugar": `translate(${RAIO * Math.sin(angulo)}px, ${-RAIO * Math.cos(angulo)}px)`,
                "--recolhido": recolhido,
                transitionDelay: !saindo && escalonar ? `${i * ESCALONAMENTO_MS}ms` : "0ms",
              } as CSSProperties
            }
          >
            <button
              ref={(el) => {
                tons.current[i] = el;
              }}
              type="button"
              onClick={() => onEscolher(`${familia.chave}-${i + 1}`)}
              aria-label={`${familia.nome}, tom ${i + 1} de 8`}
              aria-pressed={i === indiceEscolhido}
              style={{ backgroundColor: tom.hex }}
              className={`block h-full w-full rounded-pill border border-black/15 dark:border-white/15 transition-transform duration-hover ease-brand active:scale-[0.96] [@media(hover:hover)_and_(pointer:fine)]:hover:scale-110 ${
                i === indiceEscolhido ? "ring-2 ring-ink ring-offset-2 ring-offset-surface" : ""
              }`}
            />
          </span>
        );
      })}
      {/* No miolo, a própria cor tocada: vira o botão de fechar. */}
      <button
        type="button"
        onClick={() => onFechar(true)}
        aria-label="Fechar os tons"
        className="absolute left-1/2 top-1/2 flex items-center justify-center rounded-pill border border-black/15 dark:border-white/15 transition-transform duration-hover ease-brand active:scale-[0.96]"
        style={{
          width: tamanho,
          height: tamanho,
          marginLeft: -tamanho / 2,
          marginTop: -tamanho / 2,
          backgroundColor: miolo.hex,
          color: miolo.on,
        }}
      >
        <X size={16} strokeWidth={2.5} aria-hidden="true" />
      </button>
    </div>
  );
}
