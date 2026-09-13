// Cores por faixa de aproveitamento vivem em lib/triagem.ts (DESIGN_TRIAGEM.md §2).

// Números sempre em formato brasileiro (vírgula decimal) — DESIGN_TRIAGEM.md §3.
export function formatarPctBR(n: number, casas = 1): string {
  return n.toFixed(casas).replace(".", ",");
}

// mm:ss com numerais tabulares — usado tanto no cronômetro por caso do
// Praticar quanto no regressivo do Simulado.
export function formatarMMSS(segundosOuMs: number, unidade: "s" | "ms" = "ms"): string {
  const totalSeg = Math.floor(unidade === "ms" ? segundosOuMs / 1000 : segundosOuMs);
  const min = Math.floor(totalSeg / 60);
  const seg = totalSeg % 60;
  return `${String(min).padStart(2, "0")}:${String(seg).padStart(2, "0")}`;
}
