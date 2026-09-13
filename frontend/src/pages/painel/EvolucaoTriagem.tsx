import { formatarPctBR } from "../../lib/format";
import type { DiaEvolucao } from "../../lib/types";

const LARGURA = 600;
const ALTURA = 150;
const X0 = 40;
const X1 = 584;
const Y0 = 14;
const Y1 = 124;

const MESES_CURTOS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];

// Faixas da triagem (DESIGN_TRIAGEM.md §2) desenhadas ao fundo do gráfico.
const FAIXAS = [
  { de: 0, ate: 40, classe: "fill-t1" },
  { de: 40, ate: 55, classe: "fill-t2" },
  { de: 55, ate: 70, classe: "fill-t3" },
  { de: 70, ate: 85, classe: "fill-t4" },
  { de: 85, ate: 100, classe: "fill-t5" },
];

function rotuloDia(iso: string, ultimo: boolean): string {
  const d = new Date(`${iso}T00:00:00`);
  const hoje = new Date();
  hoje.setHours(0, 0, 0, 0);
  if (ultimo && d.getTime() === hoje.getTime()) return "hoje";
  return `${d.getDate()} ${MESES_CURTOS[d.getMonth()]}`;
}

// Domínio do eixo com folga de 5 pontos e amplitude mínima de 30, para uma
// variação de 2 pontos não parecer um precipício.
function dominio(valores: number[]): [number, number] {
  let lo = Math.max(0, Math.floor((Math.min(...valores) - 5) / 5) * 5);
  let hi = Math.min(100, Math.ceil((Math.max(...valores) + 5) / 5) * 5);
  if (hi - lo < 30) {
    hi = Math.min(100, lo + 30);
    lo = Math.max(0, hi - 30);
  }
  return [lo, hi];
}

export function EvolucaoTriagem({ evolucao }: { evolucao: DiaEvolucao[] }) {
  const cabecalho = (
    <div className="flex items-baseline justify-between gap-3">
      <span className="rotulo text-muted">Acerto nos últimos 14 dias</span>
      <span className="text-apoio text-muted">faixas da triagem ao fundo</span>
    </div>
  );

  if (evolucao.length < 3) {
    return (
      <div className="flex flex-col gap-3 rounded-card border border-line bg-surface p-6">
        {cabecalho}
        <p className="text-corpo text-ink-2">Histórico começa a aparecer no terceiro dia de estudo.</p>
      </div>
    );
  }

  const [lo, hi] = dominio(evolucao.map((d) => d.pct_acerto));
  const y = (v: number) => Y1 - ((v - lo) / (hi - lo)) * (Y1 - Y0);
  const passo = (X1 - X0) / (evolucao.length - 1);
  const pontos = evolucao.map((d, i) => ({ x: X0 + i * passo, y: y(d.pct_acerto), dia: d }));
  const linha = pontos.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
  const ultimo = pontos[pontos.length - 1];
  const limites = [40, 55, 70, 85].filter((l) => l > lo && l < hi);
  const yRotuloUltimo = ultimo.y - 11 < Y0 ? ultimo.y + 22 : ultimo.y - 11;

  return (
    <div className="flex flex-col gap-3 rounded-card border border-line bg-surface p-6">
      {cabecalho}
      <svg
        viewBox={`0 0 ${LARGURA} ${ALTURA}`}
        className="block h-auto w-full"
        role="img"
        aria-label={`Acerto diário nos últimos dias; no último, ${formatarPctBR(ultimo.dia.pct_acerto, 0)}%.`}
      >
        {FAIXAS.map((f) => {
          const topo = Math.min(f.ate, hi);
          const base = Math.max(f.de, lo);
          if (topo <= base) return null;
          return (
            <rect key={f.de} x={X0} y={y(topo)} width={X1 - X0} height={y(base) - y(topo)} className={f.classe} fillOpacity={0.13} />
          );
        })}
        {limites.map((l) => (
          <text key={l} x={0} y={y(l) + 3.5} fontSize={10} className="fill-muted">
            {l}%
          </text>
        ))}
        <polyline points={linha} fill="none" strokeWidth={2.5} strokeLinejoin="round" strokeLinecap="round" className="stroke-ink" />
        {pontos.map((p) => (
          <circle key={p.dia.dia} cx={p.x} cy={p.y} r={9} fill="transparent">
            <title>{`${rotuloDia(p.dia.dia, false)}: ${formatarPctBR(p.dia.pct_acerto, 0)}% (${p.dia.acertos} de ${p.dia.total})`}</title>
          </circle>
        ))}
        <circle cx={ultimo.x} cy={ultimo.y} r={5.5} strokeWidth={2} pointerEvents="none" className="fill-ink stroke-surface" />
        <text x={ultimo.x - 10} y={yRotuloUltimo} textAnchor="end" fontSize={13} fontWeight={700} className="fill-ink">
          {formatarPctBR(ultimo.dia.pct_acerto, 0)}%
        </text>
        <text x={X0} y={ALTURA - 2} fontSize={10} className="fill-muted">
          {rotuloDia(evolucao[0].dia, false)}
        </text>
        <text x={X1} y={ALTURA - 2} textAnchor="end" fontSize={10} className="fill-muted">
          {rotuloDia(ultimo.dia.dia, true)}
        </text>
      </svg>
    </div>
  );
}
