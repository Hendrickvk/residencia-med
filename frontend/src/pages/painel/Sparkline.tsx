import { corSemanticaPct } from "../../lib/format";

interface Props {
  valores: number[]; // % de acerto por dia, em ordem cronológica
}

const LARGURA = 140;
const ALTURA = 48;

const CORES: Record<ReturnType<typeof corSemanticaPct>, string> = {
  correct: "var(--correct)",
  warn: "var(--warn)",
  wrong: "var(--wrong)",
};

// REDESIGN.md §4.1: "sem eixos, sem grade, com apenas o último ponto
// marcado e rotulado" — o rótulo numérico fica a cargo de quem usa este
// componente (DiagnosticoPanel), este só desenha a linha e o ponto.
export function Sparkline({ valores }: Props) {
  if (valores.length < 2) return null;

  const min = Math.min(...valores);
  const max = Math.max(...valores);
  const span = max - min || 1;
  const passo = LARGURA / (valores.length - 1);

  const pontos = valores.map((v, i) => [i * passo, ALTURA - ((v - min) / span) * ALTURA] as const);
  const linha = pontos.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const [xUlt, yUlt] = pontos[pontos.length - 1];

  return (
    <svg width={LARGURA} height={ALTURA} viewBox={`0 0 ${LARGURA} ${ALTURA}`} className="overflow-visible">
      <polyline points={linha} fill="none" stroke="var(--ink-300)" strokeWidth={1.5} />
      <circle cx={xUlt} cy={yUlt} r={3} fill={CORES[corSemanticaPct(valores[valores.length - 1])]} />
    </svg>
  );
}
