import { ArrowRight } from "lucide-react";
import { formatarPctBR } from "../../lib/format";
import { atraso } from "../../lib/movimento";
import { CLASSES_NIVEL, MINIMO_AMOSTRA, nivelTriagem } from "../../lib/triagem";
import type { DesempenhoTipo } from "../../lib/types";

// Diferença, em pontos percentuais, a partir da qual um tipo vira "ponto fraco".
const DIFERENCA_RELEVANTE = 15;

interface Props {
  tipos: DesempenhoTipo[];
  onPraticar: (tipo: string) => void;
}

const pct = (t: DesempenhoTipo) => (100 * t.acertos) / t.total;

// DESIGN_TRIAGEM.md §6, Painel ("Por tipo de pergunta", db.desempenho_por_tipo):
// o mesmo acerto do quadro, separado pelo que a questão pede.
export function PorTipoPergunta({ tipos, onPraticar }: Props) {
  // Mesmo limite do quadro: com menos respostas, percentual não é informação.
  const comAmostra = tipos.filter((t) => t.total >= MINIMO_AMOSTRA).sort((a, b) => pct(a) - pct(b));
  const pior = comAmostra[0];
  const melhor = comAmostra[comAmostra.length - 1];
  const pontoFraco = pior && melhor && pct(melhor) - pct(pior) >= DIFERENCA_RELEVANTE;

  return (
    <section className="flex flex-col gap-4 rounded-card border border-line bg-surface p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <span className="rotulo text-muted">Por tipo de pergunta</span>
        <span className="text-apoio text-muted">o que a questão pede: diagnóstico, exame, conduta ou conceito</span>
      </div>
      {pontoFraco && (
        <p className="text-corpo text-ink-2">
          Seu ponto fraco é {pior.tipo.toLowerCase()}: {formatarPctBR(pct(pior), 0)}% de acerto, contra{" "}
          {formatarPctBR(pct(melhor), 0)}% em {melhor.tipo.toLowerCase()}.
        </p>
      )}
      <ul className="grid grid-cols-1 gap-x-8 gap-y-4 sm:grid-cols-2 lg:grid-cols-4">
        {tipos.map((t, i) => {
          const suficiente = t.total >= MINIMO_AMOSTRA;
          return (
            <li key={t.tipo}>
              <button
                type="button"
                onClick={() => onPraticar(t.tipo)}
                className="group flex w-full flex-col gap-1.5 text-left"
                aria-label={`Praticar 10 casos de ${t.tipo.toLowerCase()}`}
              >
                <span className="flex items-baseline justify-between gap-3">
                  <span className="text-corpo font-semibold text-ink">{t.tipo}</span>
                  <span className="text-apoio tabular-nums">
                    {suficiente && <span className="font-semibold text-ink">{formatarPctBR(pct(t), 0)}% </span>}
                    <span className="text-muted">
                      {t.acertos.toLocaleString("pt-BR")}/{t.total}
                    </span>
                  </span>
                </span>
                <span className="block h-1 overflow-hidden rounded-[2px] bg-line-soft">
                  {suficiente && (
                    <span
                      className={`block h-1 origin-left animate-crescer ${CLASSES_NIVEL[nivelTriagem(pct(t))].cheio}`}
                      style={{ width: `${pct(t)}%`, ...atraso(i + 2, 60) }}
                    />
                  )}
                </span>
                <span className="flex items-center gap-1 text-apoio text-muted transition-colors duration-hover group-hover:text-ink">
                  {suficiente ? "Praticar 10" : "Pouca evidência · praticar 10"}
                  <ArrowRight
                    size={14}
                    strokeWidth={2}
                    className="transition-transform duration-toggle ease-suave group-hover:translate-x-0.5"
                  />
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
