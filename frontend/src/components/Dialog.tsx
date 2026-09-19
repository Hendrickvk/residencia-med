import { useEffect, useId, useRef, useState } from "react";
import { usePresenca } from "../lib/movimento";

// Ordem de tabulação de dentro da caixa. `[tabindex="-1"]` fica fora: é
// focável por código, não pelo Tab.
const FOCAVEIS = 'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

interface Props {
  titulo: string;
  aberto: boolean;
  onFechar: () => void;
  children: React.ReactNode;
}

// Esc ou clique fora fecha qualquer camada sobreposta, e enquanto está aberta
// o foco fica preso dentro dela: sem isso o Tab passeava pela página atrás, que
// para quem navega por teclado ou leitor de tela é o diálogo não existir.
export function Dialog({ titulo, aberto, onFechar, children }: Props) {
  const idTitulo = useId();
  const { montado, saindo } = usePresenca(aberto);
  // Durante a saída mostra o último conteúdo aberto: quem abre o diálogo
  // costuma limpar o estado que o preenche (ex.: a prova escolhida) ao fechar,
  // e o texto trocaria enquanto a caixa some.
  const [ultimoAberto, setUltimoAberto] = useState({ titulo, children });
  if (aberto && (ultimoAberto.titulo !== titulo || ultimoAberto.children !== children)) {
    setUltimoAberto({ titulo, children });
  }
  const conteudo = aberto ? { titulo, children } : ultimoAberto;

  const caixa = useRef<HTMLDivElement>(null);
  // `onFechar` normalmente é uma função nova em cada render do pai. Guardada em
  // ref, o efeito depende só de `aberto` — senão ele se remontaria a cada
  // render e devolveria o foco ao primeiro campo no meio da digitação.
  const fechar = useRef(onFechar);
  useEffect(() => {
    fechar.current = onFechar;
  }, [onFechar]);

  useEffect(() => {
    if (!aberto) return;
    const anterior = document.activeElement as HTMLElement | null;
    const focaveis = () =>
      [...(caixa.current?.querySelectorAll<HTMLElement>(FOCAVEIS) ?? [])].filter(
        (el) => el.offsetParent !== null,
      );
    (focaveis()[0] ?? caixa.current)?.focus();

    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        fechar.current();
        return;
      }
      if (e.key !== "Tab" || !caixa.current) return;
      const lista = focaveis();
      if (!lista.length) return;
      const primeiro = lista[0];
      const ultimo = lista[lista.length - 1];
      const foco = document.activeElement;
      const fora = !caixa.current.contains(foco);
      if (e.shiftKey ? fora || foco === primeiro : fora || foco === ultimo) {
        e.preventDefault();
        (e.shiftKey ? ultimo : primeiro).focus();
      }
    }
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      // Devolve o foco a quem abriu: o botão continua sendo o lugar de onde a
      // pessoa saiu.
      anterior?.focus?.();
    };
  }, [aberto]);

  if (!montado) return null;

  return (
    <div className={`fixed inset-0 z-50 flex items-center justify-center p-4 ${saindo ? "pointer-events-none" : ""}`}>
      <div
        className={`absolute inset-0 bg-black/50 ${saindo ? "animate-desvanecer-saida" : "animate-desvanecer"}`}
        onClick={onFechar}
        aria-hidden="true"
      />
      <div
        ref={caixa}
        role="dialog"
        aria-modal="true"
        aria-labelledby={idTitulo}
        tabIndex={-1}
        className={`relative w-full max-w-md rounded-caso border border-line bg-surface p-6 focus:outline-none ${
          saindo ? "animate-sumir" : "animate-surgir"
        }`}
      >
        <h2 id={idTitulo} className="mb-3 text-subtitulo">
          {conteudo.titulo}
        </h2>
        {conteudo.children}
      </div>
    </div>
  );
}
