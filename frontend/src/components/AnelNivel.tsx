import type { Me } from "../lib/types";
import { Avatar } from "./Avatar";

// O avatar da barra superior com o anel do nível em volta: o avatar encolhe de 36
// para 28px dentro dos mesmos 36, e a barra não perde largura nenhuma, o que no
// celular não sobra. `pathLength` deixa o traço em 0 a 100, sem conta de raio.
export function AnelNivel({ me }: { me: Me | undefined }) {
  const pct = me?.progresso?.pct ?? 0;
  return (
    <span className="relative flex h-9 w-9 shrink-0 items-center justify-center">
      <svg viewBox="0 0 36 36" className="absolute inset-0 h-full w-full -rotate-90" aria-hidden="true">
        <circle cx="18" cy="18" r="16.75" fill="none" strokeWidth="2.5" className="stroke-line" />
        <circle
          cx="18"
          cy="18"
          r="16.75"
          fill="none"
          strokeWidth="2.5"
          strokeLinecap="round"
          pathLength={100}
          strokeDasharray="100"
          strokeDashoffset={100 - pct}
          className="stroke-ink transition-[stroke-dashoffset] duration-cresce ease-suave"
        />
      </svg>
      <Avatar me={me} tamanho={28} />
    </span>
  );
}
