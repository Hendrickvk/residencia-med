import { useEffect, useId, useState } from "react";
import { usePresenca } from "../lib/movimento";

interface Props {
  titulo: string;
  aberto: boolean;
  onFechar: () => void;
  children: React.ReactNode;
}

// Esc ou clique fora fecha qualquer camada sobreposta.
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

  useEffect(() => {
    if (!aberto) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onFechar();
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [aberto, onFechar]);

  if (!montado) return null;

  return (
    <div className={`fixed inset-0 z-50 flex items-center justify-center p-4 ${saindo ? "pointer-events-none" : ""}`}>
      <div
        className={`absolute inset-0 bg-black/50 ${saindo ? "animate-desvanecer-saida" : "animate-desvanecer"}`}
        onClick={onFechar}
        aria-hidden="true"
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={idTitulo}
        className={`relative w-full max-w-md rounded-caso border border-line bg-surface p-6 ${
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
