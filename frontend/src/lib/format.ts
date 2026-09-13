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

// Duração de prova em texto corrido: "4h51min", "5h", "45min".
export function formatarDuracaoMin(minutos: number): string {
  const total = Math.max(0, Math.round(minutos));
  const horas = Math.floor(total / 60);
  const min = total % 60;
  if (horas === 0) return `${min}min`;
  return min === 0 ? `${horas}h` : `${horas}h${String(min).padStart(2, "0")}min`;
}

// Cronômetro regressivo do Simulado: h:mm:ss a partir de 1 hora (uma prova
// oficial inteira passa de 4 horas), mm:ss abaixo disso.
export function formatarTempoRestante(segundos: number): string {
  const total = Math.max(0, Math.floor(segundos));
  const horas = Math.floor(total / 3600);
  const mmss = formatarMMSS(total % 3600, "s");
  return horas > 0 ? `${horas}:${mmss}` : mmss;
}
