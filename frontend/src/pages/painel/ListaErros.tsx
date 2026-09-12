import { useState } from "react";
import { BarraDesempenho } from "../../components/BarraDesempenho";
import { formatarPctBR } from "../../lib/format";
import type { AreaDesempenho } from "../../lib/types";

interface Props {
  areas: AreaDesempenho[];
  onClicarArea: (areaId: number) => void;
  onPraticarArea: (areaId: number) => void;
}

const MINIMO_AMOSTRA = 5;

// REDESIGN.md §4.1: "uma lista onde a própria linha é a barra" — nada de
// gráfico de barras verticais com rótulo girado.
export function ListaErros({ areas, onClicarArea, onPraticarArea }: Props) {
  const [mostrarInsuficientes, setMostrarInsuficientes] = useState(false);
  const suficientes = areas.filter((a) => a.total >= MINIMO_AMOSTRA);
  const insuficientes = areas.filter((a) => a.total < MINIMO_AMOSTRA);

  return (
    <div>
      {suficientes.length === 0 ? (
        <p className="text-corpo text-ink-500">Nenhuma área com volume suficiente ainda.</p>
      ) : (
        <div className="space-y-2">
          {suficientes.map((a) => (
            <div key={a.area_id} onClick={() => onClicarArea(a.area_id)} className="cursor-pointer">
              <BarraDesempenho
                label={a.area}
                pct={a.pct_acerto}
                fracao={`${a.acertos}/${a.total}`}
                className="transition-hover hover:border-action"
                acao={
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onPraticarArea(a.area_id);
                    }}
                    className="hidden rounded-btn border border-action bg-surface px-2.5 py-1 text-apoio text-action group-hover:block"
                  >
                    Praticar 10 desta área
                  </button>
                }
              />
            </div>
          ))}
        </div>
      )}

      {insuficientes.length > 0 && (
        <div className="mt-3">
          <button
            type="button"
            onClick={() => setMostrarInsuficientes((v) => !v)}
            className="text-apoio text-ink-500 underline decoration-dotted underline-offset-2"
          >
            Amostra insuficiente ({insuficientes.length})
          </button>
          {mostrarInsuficientes && (
            <div className="mt-2 space-y-1">
              {insuficientes.map((a) => (
                <div key={a.area_id} className="text-apoio text-ink-500">
                  {a.area} — {formatarPctBR(a.pct_acerto)}% ({a.acertos}/{a.total})
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
