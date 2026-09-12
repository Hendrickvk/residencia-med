interface Props {
  pct: number;
  label: string;
  tamanho?: number;
}

const ESPESSURA = 4;

export function AnelProgresso({ pct, label, tamanho = 64 }: Props) {
  const raio = (tamanho - ESPESSURA) / 2;
  const circunferencia = 2 * Math.PI * raio;
  const offset = circunferencia * (1 - Math.min(Math.max(pct, 0), 100) / 100);
  const centro = tamanho / 2;

  return (
    <svg width={tamanho} height={tamanho} viewBox={`0 0 ${tamanho} ${tamanho}`}>
      {/* gira só o grupo dos círculos, pra o arco começar no topo — o texto
          central fica de pé, sem herdar a rotação */}
      <g transform={`rotate(-90 ${centro} ${centro})`}>
        <circle cx={centro} cy={centro} r={raio} fill="none" stroke="var(--line)" strokeWidth={ESPESSURA} />
        <circle
          cx={centro}
          cy={centro}
          r={raio}
          fill="none"
          stroke="var(--action)"
          strokeWidth={ESPESSURA}
          strokeDasharray={circunferencia}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-[stroke-dashoffset] duration-toggle ease-brand"
        />
      </g>
      <text
        x={centro}
        y={centro}
        textAnchor="middle"
        dominantBaseline="central"
        className="fill-ink-700 font-mono text-[11px] font-medium tabular-nums"
      >
        {label}
      </text>
    </svg>
  );
}
