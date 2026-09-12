import { useEffect } from "react";

interface Props {
  titulo: string;
  aberto: boolean;
  onFechar: () => void;
  children: React.ReactNode;
}

// REDESIGN.md §8: "Esc fecha qualquer camada sobreposta."
export function Dialog({ titulo, aberto, onFechar, children }: Props) {
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-panel border border-line bg-surface p-6">
        <h2 className="mb-3 text-h2 text-ink-700">{titulo}</h2>
        {children}
      </div>
    </div>
  );
}
