import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { NumeroAnimado } from "../../components/NumeroAnimado";
import { BOTAO_PRIMARIO } from "../../lib/estilos";
import { estimarDuracao } from "../../lib/prazo";
import { definirMetaRevisao } from "../../lib/revisao";
import type { PainelData } from "../../lib/types";
import { PrevisaoSemana } from "./PrevisaoSemana";

const METAS = [10, 20, 30, 50];

interface Props {
  revisao: PainelData["revisao"];
  onRevisar: () => void;
}

// DESIGN_TRIAGEM.md §6, Painel item 4: casos de hoje dentro da meta diária,
// duração estimada e a carga dos próximos 7 dias.
export function FilaRevisao({ revisao, onRevisar }: Props) {
  const queryClient = useQueryClient();
  const [salvando, setSalvando] = useState(false);
  const { hoje, meta, feitas_hoje, excedente, segundos_por_caso, proximos_dias } = revisao;
  const opcoes = METAS.includes(meta) ? METAS : [...METAS, meta].sort((a, b) => a - b);

  async function mudarMeta(nova: number) {
    setSalvando(true);
    try {
      await definirMetaRevisao(nova);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["painel"] }),
        queryClient.invalidateQueries({ queryKey: ["me"] }),
        queryClient.invalidateQueries({ queryKey: ["revisao-leva"] }),
      ]);
    } finally {
      setSalvando(false);
    }
  }

  let situacao: string | null = null;
  if (hoje === 0) {
    if (excedente > 0) {
      situacao = `Meta de hoje cumprida: ${feitas_hoje} caso${feitas_hoje !== 1 ? "s" : ""} revisado${feitas_hoje !== 1 ? "s" : ""}. Outros ${excedente} podem esperar até amanhã.`;
    } else if (feitas_hoje > 0) {
      situacao = `Tudo revisado por hoje: ${feitas_hoje} caso${feitas_hoje !== 1 ? "s" : ""}.`;
    } else {
      situacao = "Nenhuma questão vencida hoje. As que você errar voltam para cá.";
    }
  }

  return (
    <div className="flex flex-col gap-4 rounded-card border border-line bg-surface p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <span className="rotulo text-muted">Fila de revisão</span>
        <label htmlFor="meta-revisao" className="flex items-center gap-2 text-apoio text-muted">
          Meta diária
          <select
            id="meta-revisao"
            value={meta}
            disabled={salvando}
            onChange={(e) => void mudarMeta(Number(e.target.value))}
            className="h-8 rounded-btn border border-line bg-surface px-2 text-apoio font-semibold tabular-nums text-ink outline-none transition duration-hover focus:border-ink disabled:opacity-60"
          >
            {opcoes.map((m) => (
              <option key={m} value={m}>
                {m} casos
              </option>
            ))}
          </select>
        </label>
      </div>

      {situacao ? (
        <p className="text-corpo text-ink-2">{situacao}</p>
      ) : (
        <div className="flex items-baseline gap-3.5">
          <NumeroAnimado className="num-lg" valor={hoje} formatar={(v) => String(Math.round(v))} chave="painel-fila" />
          <div className="flex flex-col">
            <span className="text-corpo leading-snug text-ink-2">
              {hoje === 1 ? "caso para hoje" : "casos para hoje"} · {estimarDuracao(hoje, segundos_por_caso)}
            </span>
            {excedente > 0 && (
              <span className="text-apoio text-muted">
                {excedente} {excedente === 1 ? "pode" : "podem"} esperar até amanhã
              </span>
            )}
          </div>
        </div>
      )}

      <PrevisaoSemana dias={proximos_dias} meta={meta} />

      {/* Sempre habilitado: com a fila vazia, a Revisão diz quando vence a próxima
          leva, e com a meta cumprida oferece "Revisar mais". */}
      <button type="button" onClick={onRevisar} className={`${BOTAO_PRIMARIO} mt-auto w-full`}>
        Revisar agora
      </button>
    </div>
  );
}
