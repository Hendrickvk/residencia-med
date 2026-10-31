import { Link } from "react-router-dom";
import { BarraNivel } from "../../components/BarraNivel";
import { formatarNumeroBR } from "../../lib/format";
import type { ProgressoNivel } from "../../lib/types";

// Uma linha só, abaixo da Conduta de hoje, sem botão primário: o dela é o único da
// tela (DESIGN_TRIAGEM.md §6). A faixa inteira é o caminho para o Progresso.
export function FaixaProgresso({ progresso }: { progresso: ProgressoNivel }) {
  return (
    <Link
      to="/progresso"
      className="flex flex-wrap items-center gap-x-5 gap-y-2 rounded-card border border-line bg-surface px-5 py-3.5 transition duration-hover ease-brand hover:border-muted sm:px-6"
    >
      <span className="whitespace-nowrap text-corpo font-semibold text-ink">
        Nível {progresso.nivel} · {progresso.patente}
      </span>
      <span className="min-w-[80px] flex-1">
        <BarraNivel pct={progresso.pct} fina />
      </span>
      <span className="whitespace-nowrap text-apoio tabular-nums text-muted">
        Faltam {formatarNumeroBR(progresso.falta)} XP para o nível {progresso.nivel + 1}
      </span>
    </Link>
  );
}
