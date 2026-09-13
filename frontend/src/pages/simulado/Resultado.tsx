import { ChevronDown, RotateCcw } from "lucide-react";
import { useState } from "react";
import { BOTAO_PRIMARIO } from "../../lib/estilos";
import { formatarPctBR } from "../../lib/format";
import { useDesempenhoSimulado, useItensSimulado, useSimulado } from "../../lib/simulados";
import { CLASSES_NIVEL, NIVEIS, nivelTriagem } from "../../lib/triagem";
import { AlternativaLinha, type EstadoAlternativa } from "../praticar/AlternativaLinha";

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
    return (
      <div className="mx-auto flex max-w-[840px] flex-col gap-6">
        <div className="h-[110px] animate-pulse rounded-card bg-line-soft" />
        <div className="h-[160px] animate-pulse rounded-caso bg-line-soft" />
        <div className="h-[320px] animate-pulse rounded-caso bg-line-soft" />
      </div>
    );
  }

  const total = simulado.num_questoes;
  const acertos = simulado.acertos ?? 0;
  const respondidas = simulado.total_respondidas ?? 0;
  const pct = total ? Math.round((100 * acertos) / total) : 0;
  const nivel = nivelTriagem(pct);
  const areas = [...(desempenho ?? [])].sort((a, b) => a.pct_acerto - b.pct_acerto);

  function alternar(itemId: number) {
    setAbertos((prev) => {
      const novo = new Set(prev);
      if (novo.has(itemId)) novo.delete(itemId);
      else novo.add(itemId);
      return novo;
    });
  }

  return (
    <div className="mx-auto flex max-w-[840px] flex-col gap-6">
      <div className="flex flex-col gap-2">
        <span className="rotulo text-muted">Resultado do simulado</span>
        <h1 className="text-titulo">
          {acertos} de {total} questões certas.
        </h1>
      </div>

      <div className="grid grid-cols-1 divide-y divide-line-soft rounded-caso border border-line bg-surface sm:grid-cols-3 sm:divide-x sm:divide-y-0">
        <div className="flex flex-col gap-2 p-6">
          <span className="rotulo text-muted">Aproveitamento</span>
          <span className="num-lg">{pct}%</span>
          <span className={`rotulo self-start rounded-etq px-2 py-1 text-[12px] ${CLASSES_NIVEL[nivel].cheio} ${CLASSES_NIVEL[nivel].texto}`}>
            {NIVEIS[nivel - 1].nome}
          </span>
        </div>
        <div className="flex flex-col gap-2 p-6">
          <span className="rotulo text-muted">Respondidas</span>
          <span className="num-lg">{respondidas}</span>
        </div>
        <div className="flex flex-col gap-2 p-6">
          <span className="rotulo text-muted">Em branco</span>
          <span className="num-lg">{Math.max(total - respondidas, 0)}</span>
        </div>
      </div>

      {areas.length > 0 && (
        <div className="flex flex-col gap-3">
          <h2 className="text-bloco">Desempenho por área neste simulado</h2>
          <div className="rounded-caso border border-line bg-surface">
            {areas.map((d) => {
              const nv = nivelTriagem(d.pct_acerto);
              return (
                <div
                  key={d.area}
                  className="grid grid-cols-[minmax(0,1fr)_minmax(80px,200px)_52px_48px] items-center gap-4 border-b border-line-soft px-5 py-3 last:border-0"
                >
                  <span className="truncate text-corpo">{d.area}</span>
                  <div className="h-1 overflow-hidden rounded-[2px] bg-line-soft">
                    <div className={`h-1 ${CLASSES_NIVEL[nv].cheio}`} style={{ width: `${d.pct_acerto}%` }} />
                  </div>
                  <span className="text-right text-apoio font-semibold tabular-nums">{formatarPctBR(d.pct_acerto, 0)}%</span>
                  <span className="text-right text-apoio tabular-nums text-muted">
                    {d.acertos}/{d.total}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="flex flex-col gap-3">
        <h2 className="text-bloco">Revisão completa</h2>
        <div className="flex flex-col gap-2">
          {itens.map((item) => {
            const aberto = abertos.has(item.item_id);
            const naoRespondida = item.resposta_dada === null;
            const acertou = item.correta === 1;

            return (
              <div key={item.item_id} className="rounded-card border border-line bg-surface">
                <button
                  type="button"
                  onClick={() => alternar(item.item_id)}
                  aria-expanded={aberto}
                  className="grid w-full grid-cols-[92px_auto_minmax(0,1fr)_auto] items-center gap-3 px-4 py-3 text-left"
                >
                  {naoRespondida ? (
                    <span className="rotulo rounded-etq border border-line px-2 py-1 text-center text-[12px] text-muted">Em branco</span>
                  ) : acertou ? (
                    <span className="rotulo rounded-etq bg-t4 px-2 py-1 text-center text-[12px] text-t4-on">Correta</span>
                  ) : (
                    <span className="rotulo rounded-etq bg-t1 px-2 py-1 text-center text-[12px] text-t1-on">Errada</span>
                  )}
                  <span className="text-[14px] font-semibold tabular-nums">Questão {item.ordem + 1}</span>
                  <span className="truncate text-corpo text-ink-2">{item.enunciado}</span>
                  <ChevronDown
                    size={16}
                    strokeWidth={2}
                    className={`shrink-0 text-muted transition-transform duration-toggle ${aberto ? "rotate-180" : ""}`}
                  />
                </button>
                {aberto && (
                  <div className="flex flex-col gap-5 border-t border-line-soft p-5 md:px-6">
                    <p className="max-w-[68ch] text-enunciado text-ink">{item.enunciado}</p>
                    <div className="flex flex-col gap-2">
                      {Object.keys(item.alternativas).map((letra) => {
                        let estado: EstadoAlternativa = "neutra";
                        if (item.resposta_correta && letra === item.resposta_correta) estado = "correta";
                        else if (letra === item.resposta_dada) estado = "errada";
                        return (
                          <AlternativaLinha key={letra} letra={letra} texto={item.alternativas[letra]} estado={estado} disabled />
                        );
                      })}
                    </div>
                    {item.explicacao && (
                      <div className="flex flex-col gap-2 border-t border-line-soft pt-5">
                        <span className="rotulo text-muted">Comentário</span>
                        <p className="max-w-[66ch] text-[16.5px] leading-[1.7] text-ink-2">{item.explicacao}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div>
        <button type="button" onClick={onNovoSimulado} className={BOTAO_PRIMARIO}>
          <RotateCcw size={16} strokeWidth={2} />
          Novo simulado
        </button>
      </div>
    </div>
  );
}
