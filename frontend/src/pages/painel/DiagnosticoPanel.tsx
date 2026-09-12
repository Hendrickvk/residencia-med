import { classesTextoPct, formatarPctBR } from "../../lib/format";
import type { AreaDesempenho, DiaEvolucao } from "../../lib/types";
import { AnelProgresso } from "./AnelProgresso";
import { Sparkline } from "./Sparkline";

const META_DIARIA = 20;

interface Props {
  totalResp: number;
  totalAcertos: number;
  pctGeral: number;
  porArea: AreaDesempenho[];
  evolucao: DiaEvolucao[];
  respondidasHoje: number;
  onContinuar: () => void;
}

// REDESIGN.md §4.1: painel único, três faixas (40/35/25%), sem cartões
// idênticos empilhados — o elemento de mais ousadia visual do produto.
export function DiagnosticoPanel({
  totalResp,
  totalAcertos,
  pctGeral,
  porArea,
  evolucao,
  respondidasHoje,
  onContinuar,
}: Props) {
  const frase =
    totalResp < 50
      ? `Volume ainda baixo para conclusões. Responda ${50 - totalResp} questões para o diagnóstico ficar confiável.`
      : `${totalAcertos} acertos em ${totalResp} questões. ${porArea[0]?.area} é a sua maior lacuna.`;

  const valoresSpark = evolucao.map((d) => d.pct_acerto);
  const temHistorico = valoresSpark.length >= 3;
  const ultimoValor = valoresSpark[valoresSpark.length - 1];
  const pctMeta = Math.round((100 * Math.min(respondidasHoje, META_DIARIA)) / META_DIARIA);

  return (
    <div className="grid grid-cols-1 divide-y divide-line rounded-panel border border-line bg-surface md:grid-cols-[40%_35%_25%] md:divide-x md:divide-y-0">
      <div className="p-6">
        <div className="text-display text-ink-700">{formatarPctBR(pctGeral)}%</div>
        <p className="mt-2 text-corpo text-ink-500">{frase}</p>
      </div>

      <div className="p-6">
        <div className="text-apoio text-ink-500">Últimos 14 dias</div>
        {temHistorico ? (
          <div className="mt-3 flex items-center gap-3">
            <Sparkline valores={valoresSpark} />
            <span className={`font-mono text-h2 tabular-nums ${classesTextoPct(ultimoValor)}`}>
              {formatarPctBR(ultimoValor)}%
            </span>
          </div>
        ) : (
          <p className="mt-3 text-corpo text-ink-500">Histórico começa a aparecer no terceiro dia de estudo.</p>
        )}
      </div>

      <div className="flex flex-col items-center justify-center gap-3 p-6">
        <AnelProgresso pct={pctMeta} label={`${respondidasHoje}/${META_DIARIA}`} />
        <p className="text-apoio text-ink-500">Meta do dia</p>
        <button
          type="button"
          onClick={onContinuar}
          className="h-9 w-full rounded-btn border border-line px-3 text-apoio text-ink-700 transition-hover hover:border-ink-300"
        >
          Continuar de onde parei
        </button>
      </div>
    </div>
  );
}
