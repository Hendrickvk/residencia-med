import { ChevronDown, RotateCcw } from "lucide-react";
import { useState } from "react";
import { NumeroAnimado } from "../../components/NumeroAnimado";
import { TextoDiscussao } from "../../components/TextoDiscussao";
import { API_URL } from "../../lib/api";
import { BOTAO_PRIMARIO } from "../../lib/estilos";
import { formatarPctBR } from "../../lib/format";
import { atraso } from "../../lib/movimento";
import { nomeEdicao, useDesempenhoSimulado, useItensSimulado, useSimulado } from "../../lib/simulados";
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
      <div className="mx-auto flex max-w-[680px] flex-col gap-6">
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
  const nomeProva = simulado.edicao && simulado.banca ? nomeEdicao(simulado.banca, simulado.edicao) : null;

  function alternar(itemId: number) {
    setAbertos((prev) => {
      const novo = new Set(prev);
      if (novo.has(itemId)) novo.delete(itemId);
      else novo.add(itemId);
      return novo;
    });
  }

  return (
    <div className="mx-auto flex max-w-[680px] animate-desvanecer flex-col gap-6">
      <div className="flex flex-col gap-2">
        <span className="rotulo text-muted">{nomeProva ? `Resultado · ${nomeProva}` : "Resultado do simulado"}</span>
        <h1 className="text-titulo">
          {acertos} de {total} questões certas.
        </h1>
      </div>

      <div className="grid grid-cols-1 divide-y divide-line-soft rounded-caso border border-line bg-surface sm:grid-cols-3 sm:divide-x sm:divide-y-0">
        <div className="flex flex-col gap-2 p-6">
          <span className="rotulo text-muted">Aproveitamento</span>
          <NumeroAnimado className="num-lg self-start" valor={pct} formatar={(v) => `${Math.round(v)}%`} />
          <span
            className={`rotulo animate-surgir self-start rounded-etq px-2 py-1 text-[12px] ${CLASSES_NIVEL[nivel].cheio} ${CLASSES_NIVEL[nivel].texto}`}
            style={{ animationDelay: "750ms" }}
          >
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
          <h2 className="text-bloco">Desempenho por área {nomeProva ? "nesta prova" : "neste simulado"}</h2>
          <div className="rounded-caso border border-line bg-surface">
            {areas.map((d, i) => {
              const nv = nivelTriagem(d.pct_acerto);
              return (
                <div
                  key={d.area}
                  className="grid animate-entrar grid-cols-[minmax(0,1fr)_minmax(80px,200px)_52px_48px] items-center gap-4 border-b border-line-soft px-5 py-3 last:border-0"
                  style={atraso(i + 2, 50)}
                >
                  <span className="truncate text-corpo">{d.area}</span>
                  <div className="h-1 overflow-hidden rounded-[2px] bg-line-soft">
                    <div
                      className={`h-1 origin-left animate-crescer ${CLASSES_NIVEL[nv].cheio}`}
                      style={{ width: `${d.pct_acerto}%`, ...atraso(i + 4, 50) }}
                    />
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
            // Na prova oficial, o número do caderno facilita conferir com o gabarito do INEP.
            const numero = nomeProva && item.numero_prova ? item.numero_prova : item.ordem + 1;

            return (
              <div
                key={item.item_id}
                className={`rounded-card border bg-surface transition-colors duration-hover ${aberto ? "border-muted" : "border-line"}`}
              >
                <button
                  type="button"
                  onClick={() => alternar(item.item_id)}
                  aria-expanded={aberto}
                  className={`grid w-full grid-cols-[92px_auto_minmax(0,1fr)_auto] items-center gap-3 px-4 py-3 text-left transition-colors duration-hover hover:bg-ground ${
                    aberto ? "rounded-t-card" : "rounded-card"
                  }`}
                >
                  {naoRespondida ? (
                    <span className="rotulo rounded-etq border border-line px-2 py-1 text-center text-[12px] text-muted">Em branco</span>
                  ) : acertou ? (
                    <span className="rotulo rounded-etq bg-t4 px-2 py-1 text-center text-[12px] text-t4-on">Correta</span>
                  ) : (
                    <span className="rotulo rounded-etq bg-t1 px-2 py-1 text-center text-[12px] text-t1-on">Errada</span>
                  )}
                  <span className="text-[14px] font-semibold tabular-nums">Questão {numero}</span>
                  <span className="truncate text-corpo text-ink-2">{item.enunciado}</span>
                  <ChevronDown
                    size={16}
                    strokeWidth={2}
                    className={`shrink-0 text-muted transition-transform duration-desliza ease-suave ${aberto ? "rotate-180" : ""}`}
                  />
                </button>
                {aberto && (
                  <div className="flex animate-entrar flex-col gap-5 border-t border-line-soft p-5 md:px-11 md:py-7">
                    {/* Mesmo recuo lateral do cartão do caso: a linha fica no mesmo comprimento. */}
                    <p className="leitura-enunciado text-ink">{item.enunciado}</p>
                    {item.tem_imagem && (
                      <img
                        src={`${API_URL}/questoes/${item.id}/imagem`}
                        alt="Imagem da questão"
                        className="max-w-full rounded-card border border-line"
                      />
                    )}
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
                        <TextoDiscussao texto={item.explicacao} />
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
        <button type="button" onClick={onNovoSimulado} className={`group ${BOTAO_PRIMARIO}`}>
          <RotateCcw
            size={16}
            strokeWidth={2}
            className="transition-transform duration-desliza ease-suave group-hover:-rotate-[120deg]"
          />
          Novo simulado
        </button>
      </div>
    </div>
  );
}
