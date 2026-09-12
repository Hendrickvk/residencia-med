import { RefreshCw } from "lucide-react";
import { classesTextoPct } from "../../lib/format";
import type { ResumoSessao } from "../../lib/types";

interface Props {
  resumo: ResumoSessao;
  onNovaSessao: () => void;
}

export default function Resumo({ resumo, onNovaSessao }: Props) {
  const { respondidas, duracaoTotalMs } = resumo;
  const n = respondidas.length;
  const acertos = respondidas.filter((r) => r.correta).length;
  const erros = n - acertos;
  const pctAcerto = n ? Math.round((100 * acertos) / n) : 0;
  const tempoMedioSeg = n ? Math.round(respondidas.reduce((s, r) => s + r.tempoMs, 0) / n / 1000) : 0;

  const porAssunto = new Map<string, { total: number; acertos: number }>();
  for (const r of respondidas) {
    const chave = r.subtopico ?? "(sem assunto)";
    const atual = porAssunto.get(chave) ?? { total: 0, acertos: 0 };
    atual.total += 1;
    if (r.correta) atual.acertos += 1;
    porAssunto.set(chave, atual);
  }

  return (
    <div className="rounded-panel border border-line bg-surface p-6">
      <h1 className="mb-5 text-h1 text-ink-700">Resumo da sessão</h1>

      <div className="grid grid-cols-1 gap-4 border-b border-line pb-5 sm:grid-cols-3">
        <div>
          <div className="text-apoio text-ink-500">Acertos</div>
          <div className="text-h1 tabular-nums text-ink-700">
            {acertos}/{n}
          </div>
        </div>
        <div>
          <div className="text-apoio text-ink-500">% de acerto</div>
          <div className={`text-h1 tabular-nums ${classesTextoPct(pctAcerto)}`}>{n ? `${pctAcerto}%` : "—"}</div>
        </div>
        <div>
          <div className="text-apoio text-ink-500">Tempo médio por questão</div>
          <div className="text-h1 tabular-nums text-ink-700">{n ? `${tempoMedioSeg}s` : "—"}</div>
        </div>
      </div>

      {porAssunto.size > 0 && (
        <div className="mt-5">
          <div className="mb-2 text-apoio font-medium text-ink-500">Desempenho por assunto</div>
          <div className="space-y-1.5">
            {[...porAssunto.entries()].map(([assunto, v]) => {
              const pct = Math.round((100 * v.acertos) / v.total);
              return (
                <div key={assunto} className="flex items-center justify-between rounded-btn border border-line px-3 py-2">
                  <span className="text-corpo text-ink-700">{assunto}</span>
                  <span className={`font-mono text-apoio tabular-nums ${classesTextoPct(pct)}`}>
                    {pct}% ({v.acertos}/{v.total})
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {erros > 0 && (
        <p className="mt-5 text-apoio text-ink-500">
          {erros} erro{erros !== 1 && "s"} desta sessão já {erros !== 1 ? "foram adicionados" : "foi adicionado"} à
          revisão espaçada automaticamente.
        </p>
      )}

      <p className="mt-1 text-apoio text-ink-300">Duração total: {Math.round(duracaoTotalMs / 1000)}s</p>

      <button
        type="button"
        onClick={onNovaSessao}
        className="mt-5 flex h-10 items-center gap-2 rounded-btn bg-action px-4 text-sm font-medium text-white transition-hover hover:bg-action-hover"
      >
        <RefreshCw size={16} strokeWidth={1.5} />
        Nova sessão
      </button>
    </div>
  );
}
