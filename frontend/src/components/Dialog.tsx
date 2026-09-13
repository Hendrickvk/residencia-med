import { useEffect, useId } from "react";

interface Props {
  titulo: string;
  aberto: boolean;
  onFechar: () => void;
  children: React.ReactNode;
}

// Esc ou clique fora fecha qualquer camada sobreposta.
export function Dialog({ titulo, aberto, onFechar, children }: Props) {
  const idTitulo = useId();

  useEffect(() => {
    if (!aberto) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onFechar();
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [aberto, onFechar]);

  if (!aberto) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onFechar}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={idTitulo}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md rounded-caso border border-line bg-surface p-6"
      >
        <h2 id={idTitulo} className="mb-3 text-subtitulo">
          {titulo}
        </h2>
        {children}
      </div>
    </div>
  );
}
