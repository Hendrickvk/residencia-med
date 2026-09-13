import { ArrowLeft, ArrowRight } from "lucide-react";

interface Props {
  pagina: number; // 0-based
  totalPaginas: number;
  total: number;
  onMudar: (pagina: number) => void;
}

const BOTAO =
  "flex h-9 items-center gap-1.5 rounded-btn border border-line bg-surface px-3 text-apoio font-medium text-ink-2 transition duration-hover hover:border-muted hover:text-ink disabled:cursor-not-allowed disabled:text-faint disabled:hover:border-line";

export function Paginacao({ pagina, totalPaginas, total, onMudar }: Props) {
  return (
    <div className="flex items-center justify-between gap-3 text-apoio text-muted">
      <button type="button" onClick={() => onMudar(pagina - 1)} disabled={pagina <= 0} className={BOTAO}>
        <ArrowLeft size={14} strokeWidth={2} />
        Anterior
      </button>
      <span className="tabular-nums">
        Página {pagina + 1} de {Math.max(totalPaginas, 1)} · {total.toLocaleString("pt-BR")} resultado{total !== 1 ? "s" : ""}
      </span>
      <button type="button" onClick={() => onMudar(pagina + 1)} disabled={pagina >= totalPaginas - 1} className={BOTAO}>
        Próxima
        <ArrowRight size={14} strokeWidth={2} />
      </button>
    </div>
  );
}
