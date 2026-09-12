import { CheckCircle2, ChevronDown, CircleDashed, RefreshCw, XCircle } from "lucide-react";
import { useState } from "react";
import { BarraDesempenho } from "../../components/BarraDesempenho";
import { classesTextoPct, formatarPctBR } from "../../lib/format";
import { useDesempenhoSimulado, useItensSimulado, useSimulado } from "../../lib/simulados";
import { AlternativaLinha } from "../praticar/AlternativaLinha";

interface Props {
  simuladoId: number;
  onNovoSimulado: () => void;
}

export default function Resultado({ simuladoId, onNovoSimulado }: Props) {
  const { data: simulado } = useSimulado(simuladoId);
  const { data: itens } = useItensSimulado(simuladoId);
  const { data: desempenho } = useDesempenhoSimulado(simuladoId);
  const [abertos, setAbertos] = useState<Set<number>>(new Set());

  if (!simulado || !itens) {
    return <div className="h-96 animate-pulse rounded-panel bg-line/40" />;
  }

  const total = simulado.num_questoes;
  const acertos = simulado.acertos ?? 0;
  const pct = total ? Math.round((100 * acertos) / total) : 0;

  function alternar(itemId: number) {
    setAbertos((prev) => {
      const novo = new Set(prev);
      novo.has(itemId) ? novo.delete(itemId) : novo.add(itemId);
      return novo;
    });
  }

  return (
    <div>
      <h1 className="mb-5 text-h1 text-ink-700">Resultado do simulado</h1>

      <div className="grid grid-cols-1 gap-4 rounded-panel border border-line bg-surface p-6 sm:grid-cols-3">
        <div>
          <div className="text-apoio text-ink-500">Acertos</div>
          <div className="text-h1 tabular-nums text-ink-700">
            {acertos}/{total}
          </div>
        </div>
        <div>
          <div className="text-apoio text-ink-500">% de acerto</div>
          <div className={`text-h1 tabular-nums ${classesTextoPct(pct)}`}>{formatarPctBR(pct, 0)}%</div>
        </div>
        <div>
          <div className="text-apoio text-ink-500">Respondidas</div>
          <div className="text-h1 tabular-nums text-ink-700">{simulado.total_respondidas ?? 0}</div>
        </div>
      </div>

      {desempenho && desempenho.length > 0 && (
        <div className="mt-6">
          <div className="mb-3 text-corpo font-semibold text-ink-700">Desempenho por área (neste simulado)</div>
          <div className="space-y-2">
            {desempenho.map((d) => (
              <BarraDesempenho key={d.area} label={d.area} pct={d.pct_acerto} fracao={`${d.acertos}/${d.total}`} />
            ))}
          </div>
        </div>
      )}

      <div className="mt-6">
        <div className="mb-3 text-corpo font-semibold text-ink-700">Revisão completa</div>
        <div className="space-y-2">
          {itens.map((item) => {
            const aberto = abertos.has(item.item_id);
            const naoRespondida = item.resposta_dada === null;
            const Icone = naoRespondida ? CircleDashed : item.correta === 1 ? CheckCircle2 : XCircle;
            const corIcone = naoRespondida ? "text-ink-300" : item.correta === 1 ? "text-correct" : "text-wrong";
            const rotulo = naoRespondida ? "não respondida" : item.correta === 1 ? "correta" : "errada";

            return (
              <div key={item.item_id} className="rounded-panel border border-line bg-surface">
                <button
                  type="button"
                  onClick={() => alternar(item.item_id)}
                  className="flex w-full items-center gap-3 px-4 py-3 text-left"
                >
                  <Icone size={18} strokeWidth={1.5} className={`shrink-0 ${corIcone}`} />
                  <span className="flex-1 truncate text-corpo text-ink-700">
                    [{item.ordem + 1}] {rotulo} — {item.enunciado.slice(0, 80)}…
                  </span>
                  <ChevronDown
                    size={16}
                    strokeWidth={1.5}
                    className={`shrink-0 text-ink-500 transition-transform ${aberto ? "rotate-180" : ""}`}
                  />
                </button>
                {aberto && (
                  <div className="border-t border-line p-4">
                    <p className="max-w-[68ch] text-enunciado text-ink-700">{item.enunciado}</p>
                    <div className="mt-4 space-y-2">
                      {Object.keys(item.alternativas).map((letra) => {
                        let estado: "correta" | "errada" | "neutra" = "neutra";
                        if (item.resposta_correta && letra === item.resposta_correta) estado = "correta";
                        else if (letra === item.resposta_dada) estado = "errada";
                        return (
                          <AlternativaLinha
                            key={letra}
                            letra={letra}
                            texto={item.alternativas[letra]}
                            estado={estado}
                            disabled
                          />
                        );
                      })}
                    </div>
                    {item.explicacao && (
                      <div className="mt-3 rounded-btn border border-line bg-canvas p-3 text-corpo text-ink-700">
                        {item.explicacao}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <button
        type="button"
        onClick={onNovoSimulado}
        className="mt-6 flex h-10 items-center gap-2 rounded-btn bg-action px-4 text-sm font-medium text-white transition-hover hover:bg-action-hover"
      >
        <RefreshCw size={16} strokeWidth={1.5} />
        Novo simulado
      </button>
    </div>
  );
}
