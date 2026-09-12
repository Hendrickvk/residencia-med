export type CorSemantica = "correct" | "warn" | "wrong";

// Faixas do REDESIGN.md §4.1: <40% errado, 40-69% atenção, >=70% bom.
export function corSemanticaPct(pct: number): CorSemantica {
  if (pct < 40) return "wrong";
  if (pct < 70) return "warn";
  return "correct";
}

export function classesTextoPct(pct: number): string {
  return { correct: "text-correct", warn: "text-warn", wrong: "text-wrong" }[corSemanticaPct(pct)];
}

export function classesFundoSuavePct(pct: number): string {
  return { correct: "bg-correct-soft", warn: "bg-warn-soft", wrong: "bg-wrong-soft" }[corSemanticaPct(pct)];
}

// REDESIGN.md §7: números sempre em formato brasileiro (vírgula decimal).
export function formatarPctBR(n: number, casas = 1): string {
  return n.toFixed(casas).replace(".", ",");
}

// mm:ss com numerais tabulares (REDESIGN.md §4.2/§4.3) — usado tanto no
// cronômetro por questão do Praticar quanto no regressivo do Simulado.
export function formatarMMSS(segundosOuMs: number, unidade: "s" | "ms" = "ms"): string {
  const totalSeg = Math.floor(unidade === "ms" ? segundosOuMs / 1000 : segundosOuMs);
  const min = Math.floor(totalSeg / 60);
  const seg = totalSeg % 60;
  return `${String(min).padStart(2, "0")}:${String(seg).padStart(2, "0")}`;
}
