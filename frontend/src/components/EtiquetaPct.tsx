import { formatarPctBR } from "../lib/format";
import { CLASSES_NIVEL, NIVEIS, nivelTriagem } from "../lib/triagem";

// Percentual numa etiqueta na cor do nível (DESIGN_TRIAGEM.md §2), com o nome do nível no title.
export function EtiquetaPct({ pct }: { pct: number }) {
  const nivel = nivelTriagem(pct);
  return (
    <span
      title={NIVEIS[nivel - 1].nome}
      className={`rounded-etq px-2 py-1 text-center text-[13px] font-bold tabular-nums ${CLASSES_NIVEL[nivel].cheio} ${CLASSES_NIVEL[nivel].texto}`}
    >
      {formatarPctBR(pct, 0)}%
    </span>
  );
}
