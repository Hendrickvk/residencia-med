import { ArrowLeft, ArrowRight } from "lucide-react";

interface Props {
  pagina: number; // 0-based
  totalPaginas: number;
  total: number;
  onMudar: (pagina: number) => void;
}

export function Paginacao({ pagina, totalPaginas, total, onMudar }: Props) {
  return (
    <div className="flex items-center justify-between gap-3 text-apoio text-ink-500">
      <button
        type="button"
        onClick={() => onMudar(pagina - 1)}
        disabled={pagina <= 0}
        className="flex items-center gap-1 rounded-btn border border-line px-2.5 py-1.5 transition-hover hover:border-ink-300 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <ArrowLeft size={14} strokeWidth={1.5} />
        Anterior
      </button>
      <span>
        Página {pagina + 1} de {Math.max(totalPaginas, 1)} — {total} resultado(s)
      </span>
      <button
        type="button"
        onClick={() => onMudar(pagina + 1)}
        disabled={pagina >= totalPaginas - 1}
        className="flex items-center gap-1 rounded-btn border border-line px-2.5 py-1.5 transition-hover hover:border-ink-300 disabled:cursor-not-allowed disabled:opacity-50"
      >
        Próxima
        <ArrowRight size={14} strokeWidth={1.5} />
      </button>
    </div>
  );
}
