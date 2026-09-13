// Nível de triagem de uma área pelo aproveitamento (DESIGN_TRIAGEM.md §2).
// Classificação de apresentação, no mesmo espírito do limite de amostra que
// já vivia no front — se um dia alimentar regra de negócio (ex.: escolher
// questões para uma sessão), migra para db.py.

export type NivelTriagem = 1 | 2 | 3 | 4 | 5;

// Abaixo disso a área não é classificada: "50% de 1/2 não é informação".
export const MINIMO_AMOSTRA = 5;

export const NIVEIS: { nivel: NivelTriagem; nome: string; faixa: string }[] = [
  { nivel: 1, nome: "Emergência", faixa: "abaixo de 40%" },
  { nivel: 2, nome: "Muito urgente", faixa: "40 a 54%" },
  { nivel: 3, nome: "Urgente", faixa: "55 a 69%" },
  { nivel: 4, nome: "Pouco urgente", faixa: "70 a 84%" },
  { nivel: 5, nome: "Não urgente", faixa: "85% ou mais" },
];

export function nivelTriagem(pct: number): NivelTriagem {
  if (pct < 40) return 1;
  if (pct < 55) return 2;
  if (pct < 70) return 3;
  if (pct < 85) return 4;
  return 5;
}

// Classes literais por nível: o Tailwind só gera classe que aparece escrita
// por inteiro no código, então nada de montar `bg-t${n}` em tempo de execução.
export const CLASSES_NIVEL: Record<NivelTriagem, { cheio: string; suave: string; texto: string; borda: string }> = {
  1: { cheio: "bg-t1", suave: "bg-t1-soft", texto: "text-t1-on", borda: "border-t1" },
  2: { cheio: "bg-t2", suave: "bg-t2-soft", texto: "text-t2-on", borda: "border-t2" },
  3: { cheio: "bg-t3", suave: "bg-t3-soft", texto: "text-t3-on", borda: "border-t3" },
  4: { cheio: "bg-t4", suave: "bg-t4-soft", texto: "text-t4-on", borda: "border-t4" },
  5: { cheio: "bg-t5", suave: "bg-t5-soft", texto: "text-t5-on", borda: "border-t5" },
};
