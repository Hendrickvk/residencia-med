import { classesFundoSuavePct, formatarPctBR } from "../lib/format";

interface Props {
  label: string;
  pct: number;
  fracao?: string; // ex: "3/7"
  acao?: React.ReactNode; // botão que aparece só no hover (ex: "Praticar 10 desta área")
  className?: string;
}

// "A própria linha é a barra" (REDESIGN.md §4.1) — usado tanto em "Onde
// você está errando" (Painel) quanto no desempenho por área do resultado
// do Simulado, pra não duplicar a mesma construção duas vezes.
export function BarraDesempenho({ label, pct, fracao, acao, className = "" }: Props) {
  return (
    <div className={`group relative flex h-10 items-center overflow-hidden rounded-btn border border-line ${className}`}>
      <div className={`absolute inset-y-0 left-0 ${classesFundoSuavePct(pct)}`} style={{ width: `${pct}%` }} aria-hidden="true" />
      <div className="relative z-10 flex w-full items-center justify-between gap-3 px-3">
        <span className="text-corpo text-ink-700">{label}</span>
        <div className="flex items-center gap-3">
          {acao}
          <span className="font-mono text-apoio tabular-nums text-ink-500">
            {formatarPctBR(pct)}%{fracao ? ` · ${fracao}` : ""}
          </span>
        </div>
      </div>
    </div>
  );
}
